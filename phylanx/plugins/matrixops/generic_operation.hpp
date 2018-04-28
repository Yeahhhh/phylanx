// Copyright (c) 2018 Tianyi Zhang
//
// Distributed under the Boost Software License, Version 1.0. (See accompanying
// file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

#ifndef PHYLANX_GENERIC_OPERATION_HPP
#define PHYLANX_GENERIC_OPERATION_HPP

#include <phylanx/config.hpp>
#include <phylanx/execution_tree/primitives/base_primitive.hpp>
#include <phylanx/execution_tree/primitives/primitive_component_base.hpp>
#include <phylanx/ir/node_data.hpp>

#include <hpx/lcos/future.hpp>

#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace phylanx { namespace execution_tree { namespace primitives
{
    class generic_operation
      : public primitive_component_base
      , public std::enable_shared_from_this<generic_operation>
    {
    protected:
        hpx::future<primitive_argument_type> eval(
            std::vector<primitive_argument_type> const& operands,
            std::vector<primitive_argument_type> const& args) const;

        using operand_type = ir::node_data<double>;
        using operands_type = std::vector<operand_type>;

    public:
        static std::vector<match_pattern_type> const match_data;

        generic_operation() = default;

        generic_operation(std::vector<primitive_argument_type>&& operands,
            std::string const& name, std::string const& codename);

        hpx::future<primitive_argument_type> eval(
            std::vector<primitive_argument_type> const& args) const override;

    private:
        primitive_argument_type generic0d(operands_type&& ops) const;
        primitive_argument_type generic1d(operands_type&& ops) const;
        primitive_argument_type generic2d(operands_type&& ops) const;
        double (*get_0d_map(std::string const& name))(double);
        blaze::DynamicVector<double> (*get_1d_map(std::string const& name))(
            const blaze::CustomVector<double, blaze::aligned, blaze::padded>&);
        blaze::DynamicMatrix<double> (*get_2d_map(std::string const& name))(
            const blaze::CustomMatrix<double, blaze::aligned, blaze::padded>&);
        double (*func0d_)(double);
        blaze::DynamicVector<double> (*func1d_)(
            const blaze::CustomVector<double, blaze::aligned, blaze::padded>&);
        blaze::DynamicMatrix<double> (*func2d_)(
            const blaze::CustomMatrix<double, blaze::aligned, blaze::padded>&);
    };

    inline primitive create_generic_operation(hpx::id_type const& locality,
        std::vector<primitive_argument_type>&& operands,
        std::string const& name = "", std::string const& codename = "")
    {
        return create_primitive_component(
            locality, "__gen", std::move(operands), name, codename);
    }
}}}

#endif    //PHYLANX_GENERIC_OPERATION_HPP