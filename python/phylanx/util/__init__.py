# Copyright (c) 2017 Hartmut Kaiser
# Copyright (c) 2018 Steven R. Brandt
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

try:
    from _phylanx.util import *

except Exception:
    from _phylanxd.util import *

import phylanx
et = phylanx.execution_tree
import inspect, re, ast

def physl_fmt(src):
    pat = re.compile(r'"[^"]*"|\([^()]*\)|.')
    indent = 0
    for s in re.findall(pat,src):
        if s == '(':
            print(s,end="")
            indent += 1
        elif s == ')':
            indent -= 1
            print("")
            print(" " * indent * 2,end="")
            print(s,end="")
        elif s == ',':
            print(s)
            print(" " * indent * 2,end="")
        else:
            print(s,end="")
    print("")

def ast_dump(a,depth=0,label=""):
    if a == None:
        nm = "None"
    else:
        nm = a.__class__.__name__
    print("  "*depth+label,end="")
    show_children = True
    show_attrs = True
    if nm == "None":
        print("None")
        show_children = False
        show_attrs = False
    elif nm == "Num":
        if type(a.n)==int:
            print("%s=%d" % (nm,a.n))
        else:
            print("%s=%f" % (nm,a.n))
    elif nm == "Slice":
        print("Slice")
        ast_dump(a.lower,depth+1,label="lower:")
        ast_dump(a.upper,depth+1,label="upper:")
        show_children = False
    elif nm == "Str":
        print("%s='%s'" % (nm,a.s))
    elif nm == "Name":
        print("%s='%s'" %(nm,a.id))
    elif nm == "arg":
        print("%s='%s'" %(nm,a.arg))
    elif nm == "If":
        show_children = False
        print(nm)
        for n in a.body:
            ast_dump(n,depth+1)
        if len(a.orelse)>0:
            print("  "*depth,end="")
            print("Else")
            for n in a.orelse:
                ast_dump(n,depth+1)
    else:
        print(nm)
    if show_attrs:
        for (f,v) in ast.iter_fields(a):
            if type(f) == str and type(v) == str:
                print("%s:attr[%s]=%s" % ("  "*(depth+1),f,v))
    if show_children:
        if iter_children:
            for n in ast.iter_child_nodes(a):
                ast_dump(n,depth+1)

def phy_print(m):
    ndim = m.num_dimensions()
    if ndim == 1:
        for i in range(m.dimension(0)):
            print(m[i])
    elif ndim == 2:
        for i in range(m.dimension(0)):
            for j in range(m.dimension(1)):
                print("%10.2f" % m[i, j], end=" ")
                if j > 5:
                    print("...", end=" ")
                    break
            print()
            if i > 5:
                print("%10s" % "...")
                break
    elif ndim == 0:
        print(m[0])
    else:
        print("ndim=", ndim)

def get_node(node,**kwargs):
    args = [arg for arg in ast.iter_child_nodes(node)]
    params = {"name":None,"num":None}
    for k in kwargs:
        if k not in params:
            raise Exception("Invalid argument '%s'" % k)
        else:
            params[k] = kwargs[k]
    name = params["name"]
    num  = params["num"]
    if name != None:
        for i in range(len(args)):
            a = args[i]
            nm = a.__class__.__name__
            if nm == name:
                if num == None or num == i:
                    return a
    elif num != None:
        if num < len(args):
            return args[num]

class Recompiler:
    def __init__(self):
        self.defs = {}
        self.priority = 0
        self.groupAggressively = True
    def recompile(self,a,allowreturn=False):
        nm = a.__class__.__name__
        if nm == "Num":
            return str(a.n)
        elif nm == "Str":
            return '"'+a.s+'"'
        elif nm == "Name":
            return a.id
        elif nm == "Expr":
            args = [arg for arg in ast.iter_child_nodes(a)]
            s = ""
            if len(args)==1:
                s += self.recompile(args[0])
            else:
                raise Exception()
            return s
        elif nm == "FunctionDef":
            args = [arg for arg in ast.iter_child_nodes(a)]
            s = ""
            s += "define("
            s += a.name
            s += ","
            for arg in ast.iter_child_nodes(args[0]):
                s += arg.arg
                s += ","
            if len(args)==2:
                s += self.recompile(args[1],True)
            else:
                s += "block("
                #for aa in args[1:]:
                sargs = args[1:]
                for i in range(len(sargs)):
                    aa = sargs[i]
                    if i+1 == len(sargs):
                        s += self.recompile(aa,True)
                    else:
                        s += self.recompile(aa,False)
                        s += ","
                s += ")"
            s += ")," + a.name
            return s
        elif nm == "BinOp":
            args = [arg for arg in ast.iter_child_nodes(a)]
            s = ""
            save = self.priority
            nm2 = args[1].__class__.__name__
            priority = 2
            if nm2 == "Add":
                op = " + "
                priority = 1
            elif nm2 == "Sub":
                op = " - "
                priority = 1
            elif nm2 == "Mult":
                op = " * "
            elif nm2 == "Div":
                op = " / "
            elif nm2 == "Mod":
                op = " % "
            elif nm2 == "Pow":
                op = " ** "
                priority = 3
            else:
                raise Exception(nm2)
            self.priority = priority
            term1 = self.recompile(args[0])
            self.priority = priority
            term2 = self.recompile(args[2])
            if priority < save or self.groupAggressively:
                s += "(" + term1 + op + term2 + ")"
            else:
                s += term1 + op + term2
            return s
        elif nm == "Call":
            args = [arg for arg in ast.iter_child_nodes(a)]
            if args[0].id == "print":
                args[0].id = "cout"
            s = args[0].id+'('
            for n in range(1,len(args)):
                if n > 1:
                    s += ','
                s += self.recompile(args[n])
            s += ')'
            return s
        elif nm == "Module":
            args = [arg for arg in ast.iter_child_nodes(a)]
            return self.recompile(args[0])
        elif nm == "Return":
            if not allowreturn:
                raise Exception("Return only allowed at end of function: line=%d\n" % a.lineno)
            args = [arg for arg in ast.iter_child_nodes(a)]
            return " "+self.recompile(args[0])
        elif nm == "Assign":
            args = [arg for arg in ast.iter_child_nodes(a)]
            s = ""
            if args[0].id in self.defs:
                s += "store"
            else:
                s += "define"
                self.defs[args[0].id]=1
            s += "("+args[0].id+","+self.recompile(args[1])+")"
            return s
        elif nm == "AugAssign":
            args = [arg for arg in ast.iter_child_nodes(a)]
            sym = "?"
            nn = args[1].__class__.__name__
            if nn == "Add":
                sym = "+"
            return "store("+args[0].id+","+args[0].id + sym + self.recompile(args[2])+")"
        elif nm == "While":
            args = [arg for arg in ast.iter_child_nodes(a)]
            s = "while("+self.recompile(args[0])+","
            if len(args)==2:
                s += self.recompile(args[1])
            else:
                tw = "block("
                for aa in args[1:]:
                    s += tw
                    tw = ","
                    s += self.recompile(aa)
                s += ")"
            s += ")"
            return s
        elif nm == "If":
            s = "if("+self.recompile(a.test)+","
            if len(a.body)>1:
                s += "block("
                for j in range(len(a.body)):
                    aa = a.body[j]
                    if j > 0:
                        s += ","
                    if j + 1 == len(a.body):
                        s += self.recompile(aa,allowreturn)
                    else:
                        s += self.recompile(aa)
                s += ")"
            else:
                s += self.recompile(a.body[0],allowreturn)
            s += ","
            if len(a.orelse)>1:
                s += "block("
                for j in range(len(a.orelse)):
                    aa = a.orelse[j]
                    if j > 0:
                        s += ","
                    if j + 1 == len(a.orelse):
                        s += self.recompile(aa,allowreturn)
                    else:
                        s += self.recompile(aa)
                s += ")"
            elif len(a.orelse)==1:
                s += self.recompile(a.orelse[0],allowreturn)
            else:
                s += "block()"
            s += ")"
            return s
        elif nm == "Compare":
            args = [arg for arg in ast.iter_child_nodes(a)]
            sym = "?"
            nn = args[1].__class__.__name__
            if nn == "Lt":
                sym = "<"
            elif nn == "Gt":
                sym = ">"
            elif nn == "LtE":
                sym = "<="
            elif nn == "GtE":
                sym = ">="
            elif nn == "NotEq":
                sym = "!="
            elif nn == "Eq":
                sym = "=="
            return self.recompile(args[0])+sym+self.recompile(args[2])
        elif nm == "UnaryOp":
            args = [arg for arg in ast.iter_child_nodes(a)]
            nm2 = args[0].__class__.__name__
            nm3 = args[1].__class__.__name__
            if nm2 == "USub":
                if nm3 == "BinOp" or self.groupAggressively:
                    return "-(" + self.recompile(args[1])+")"
                else:
                    return "-" + self.recompile(args[1])
            else:
                raise Exception(nm2)
        elif nm == "Subscript":
            e = get_node(a,name="ExtSlice")
            s0 = get_node(e,name="Slice",num=0)
            s1 = get_node(e,name="Slice",num=1)
            xlo = s0.lower
            xhi = s0.upper
            ylo = s1.lower
            yhi = s1.upper
            sname = self.recompile(get_node(a,num=0))
            s = "slice("
            s += sname
            s += ","
            if xlo == None:
                s += "0"
            else:
                s += self.recompile(xlo)
            s += ","
            if xhi == None:
                s += "shape(" + sname + ",0)"
            else:
                s += self.recompile(xhi)
            s += ","
            if ylo == None:
                s += "0"
            else:
                s += self.recompile(ylo)
            s += ","
            if yhi == None:
                s += "shape(" + sname + ",1)"
            else:
                s += self.recompile(yhi)
            s += ")"
            return s
        else:
            raise Exception(nm)

def convert_to_phylanx_type(v):
    t = type(v)
    try:
        import numpy
        if t == numpy.ndarray:
            return et.var(v)
    except:
          pass
    if t == int or t == float or t == list or t == str:
        return et.var(v)
    else:
        return v

# Create the decorator
class phyfun(object):
    def __init__(self,f):
        self.f = f
        # Get the source code
        src = inspect.getsource(f) #getsource(f)
        # Before recompiling the code, take
        # off the decorator from the source.
        src = re.sub(r'^\s*@\w+\s*','',src)

        # Create the AST
        tree = ast.parse(src)
        r = Recompiler()
        self.__physl_src__ = "block(" + r.recompile(tree)+')\n'

    def __call__(self,*args):
        nargs = tuple(convert_to_phylanx_type(a) for a in args)
        return et.eval(self.__physl_src__,*nargs)
