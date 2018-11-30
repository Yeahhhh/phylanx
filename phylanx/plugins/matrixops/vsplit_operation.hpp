// Copyright (c) 2018 Maxwell Reeser
// Copyright (c) 2018 Parsa Amini
// Copyright (c) 2018 Hartmut Kaiser
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#if !defined(PHYLANX_EXECUTION_TREE_VSLICING_OCT_17_2018_1527PM)
#define PHYLANX_EXECUTION_TREE_SLICING_OCT_17_2018_1527PM

#include <phylanx/config.hpp>
#include <phylanx/execution_tree/primitives/base_primitive.hpp>
#include <phylanx/execution_tree/primitives/node_data_helpers.hpp>
#include <phylanx/ir/node_data.hpp>
#include <phylanx/ir/ranges.hpp>

#include <string>

namespace phylanx { namespace execution_tree { namespace primitives
{

    class vsplit_operation
      : public primitive_component_base
      , public std::enable_shared_from_this<vsplit_operation>
    {

    protected:
        hpx::future<primitive_argument_type> eval(
            primitive_arguments_type const& operands,
            primitive_arguments_type const& args,
            eval_context ctx) const;

    public:
        static match_pattern_type const match_data;

        vsplit_operation() = default;

        vsplit_operation(primitive_arguments_type&& operands,
            std::string const& name, std::string const& codename);

        hpx::future<primitive_argument_type> eval(
            primitive_arguments_type const& params, eval_context ctx) const override;

    private:
        primitive_argument_type vsplit_args(
            primitive_arguments_type&& args) const;
        primitive_argument_type vsplit_args_ind(
            ir::range&& l, primitive_arguments_type&& args) const;
/*
        template <typename T>
        primitive_argument_type vsplit0d_helper(
            primitive_arguments_type&& args) const;
        primitive_argument_type vsplit0d(
            primitive_arguments_type&& args) const;

        template <typename T>
        primitive_argument_type vsplit1d_helper(
            primitive_arguments_type&& args) const;
        primitive_argument_type vsplit1d(
            primitive_arguments_type&& args) const;
*/
        template <typename T>
        primitive_argument_type vsplit2d_helper(
            primitive_arguments_type&& args) const;
        primitive_argument_type vsplit2d(
            primitive_arguments_type&& args) const;

    private:
        node_data_type dtype_;
    };

    inline primitive create_vsplit_operation(hpx::id_type const& locality,
        primitive_arguments_type&& operands,
        std::string const& name = "", std::string const& codename = "")
    {
        return create_primitive_component(
            locality, "vsplit", std::move(operands), name, codename);
    }

}}}

#endif
