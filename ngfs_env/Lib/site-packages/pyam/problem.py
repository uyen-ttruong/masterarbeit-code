"""
Classes for modeling assortative matching boundary value problems.

@author : David R. Pugh
@date : 2015-07-14

"""
from __future__ import division
import sympy as sym

from pycollocation import SymbolicTwoPointBVPLike

from . model import AssortativeMatchingModelLike


class AssortativeMatchingProblem(AssortativeMatchingModelLike, SymbolicTwoPointBVPLike):

    def __init__(self, assortativity, input1, input2, F, F_params):
        """
        Create an instance of the MatchingProblem class.

        Parameters
        ----------
        assortativity : str
            String defining the type of matching assortativity. Must be one of
            'positive' or 'negative'.
        input1 : inputs.Input
            A heterogenous production input.
        input2 : inputs.Input
            A heterogenous production input.
        F : sympy.Basic
            Symbolic expression describing the production function.
        F_params : dict
            Dictionary of model parameters for the production function.

        """
        self.assortativity = assortativity
        self.input1 = input1
        self.input2 = input2
        self.F = F
        self.F_params = F_params

    @property
    def _subs(self):
        """Dictionary of variable substitutions"""
        subs = {self.input2.var: self._symbolic_vars[1],
                self._required_symbols[0]: self._symbolic_vars[2],
                self._required_symbols[1]: 1.0}
        return subs

    @property
    def boundary_conditions(self):
        """Boundary conditions for the matching problem."""
        if self.assortativity == "positive":
            bcs = {'lower': [self._symbolic_vars[1] - self.input1.lower],
                   'upper': [self._symbolic_vars[1] - self.input1.upper]}
        else:
            bcs = {'lower': [self._symbolic_vars[1] - self.input1.upper],
                   'upper': [self._symbolic_vars[1] - self.input1.lower]}
        return bcs

    @property
    def dependent_vars(self):
        """Return a list of model dependent variables."""
        return ['mu', 'theta']

    @property
    def f(self):
        """
        Symbolic expression for intensive output.

        :getter: Return the current expression for intensive output.
        :type: sympy.Basic.

        """
        expr = (1 / self._required_symbols[1]) * self.F
        return expr.subs(self._subs)

    @property
    def factor_payment_1(self):
        """
        Symbolic expression for payments made to input 1.

        :getter: Return the current expression for the factor payments.
        :type: sympy.Basic.

        """
        return sym.diff(self.f, self._symbolic_vars[2])

    @property
    def factor_payment_2(self):
        """
        Symbolic expression for payments made to input 2.

        :getter: Return the current expression for the factor payments.
        :type: sympy.Basic.

        """
        revenue = self.f
        costs = self._symbolic_vars[2] * self.factor_payment_1
        return revenue - costs

    @property
    def Fx(self):
        """
        Symbolic expression for the marginal product of input1.

        :getter: Return the the marginal product of input1.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input1.var)

    @property
    def Fy(self):
        """
        Symbolic expression for the marginal product of input2.

        :getter: Return the the marginal product of input2.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input2.var)

    @property
    def Fl(self):
        """
        Symbolic expression for the marginal product of l.

        :getter: Return the the marginal product of l.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self._required_symbols[0])

    @property
    def Fr(self):
        """
        Symbolic expression for the marginal product of r.

        :getter: Return the the marginal product of r.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self._required_symbols[1])

    @property
    def Fxy(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input1.var, self.input2.var)

    @property
    def Fxl(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input1.var, self._required_symbols[0])

    @property
    def Fxr(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input1.var, self._required_symbols[1])

    @property
    def Fyl(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input2.var, self._required_symbols[0])

    @property
    def Fyr(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, self.input2.var, self._required_symbols[1])

    @property
    def Flr(self):
        """
        Symbolic expression for the cross-partial derivative.

        :getter: Return the expression for the cross-partial derivative.
        :type: sympy.Basic

        """
        return sym.diff(self.F, *self._required_symbols)

    @property
    def H(self):
        """
        Ratio of input1 probability density to input2 probability density.

        :getter: Return current density ratio.
        :type: sympy.Basic

        """
        return self.input1.pdf / self.input2.pdf

    @property
    def independent_var(self):
        """Return the model independent variable as a string."""
        return 'x'

    @property
    def mu_prime(self):
        """
        ODE describing the equilibrium matching between production inputs.

        :getter: Return the current expression for mu prime.
        :type: sympy.Basic

        """
        if self.assortativity == "positive":
            expr = self.H / self._symbolic_vars[2]
        else:
            expr = expr = -self.H / self._symbolic_vars[2]
        return expr.subs(self._subs)

    @property
    def params(self):
        """
        Dictionary of model parameters.

        :getter: Return the current parameter dictionary.
        :type: dict

        """
        model_params = {}
        model_params.update(self.input1.params)
        model_params.update(self.input2.params)
        model_params.update(self.F_params)
        return self._order_params(model_params)

    @property
    def rhs(self):
        """Symbolic expressions for the RHS of the system of ODEs."""
        return {'mu': self.mu_prime, 'theta': self.theta_prime}

    @property
    def theta_prime(self):
        """
        Differential equation describing the equilibrium firm size.
        :getter: Return the current expression for theta prime.
        :type: sympy.Basic
        """
        if self.assortativity == "positive":
            expr = (self.H * self.Fyl - self.Fxr) / self.Flr
        else:
            expr = -(self.H * self.Fyl + self.Fxr) / self.Flr
        return expr.subs(self._subs)
