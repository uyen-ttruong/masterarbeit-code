"""
Classes for building assortative matchign models with heterogenous factors of
production.

@author : David R. Pugh
@date : 2015-01-24

"""
import sympy as sym

from . import inputs


class AssortativeMatchingModelLike(object):
    """Class representing a matching model with two-sided heterogeneity."""

    _required_symbols = sym.symbols(['l', 'r'])

    @property
    def assortativity(self):
        """
        String defining the matching assortativty.

        :getter: Return the current matching assortativity
        :setter: Set a new matching assortativity.
        :type: str

        """
        return self._assortativity

    @assortativity.setter
    def assortativity(self, value):
        """Set new matching assortativity."""
        self._assortativity = self._validate_assortativity(value)

    @property
    def F(self):
        """
        Symbolic expression describing the available production technology.

        :getter: Return the current production function.
        :setter: Set a new production function.
        :type: sympy.Basic

        """
        return self._F

    @F.setter
    def F(self, value):
        """Set a new production function."""
        self._F = self._validate_production_function(value)

    @property
    def F_params(self):
        """
        Dictionary of parameters for the production function, F.

        :getter: Return the current parameter dictionary.
        :type: dict

        """
        return self._F_params

    @F_params.setter
    def F_params(self, value):
        """Set a new dictionary of parameters for F."""
        self._F_params = self._validate_F_params(value)

    @property
    def input1(self):
        """
        Class describing a heterogenous production input.

        :getter: Return production input1.
        :setter: Set new production input1.
        :type: inputs.Input

        """
        return self._input1

    @input1.setter
    def input1(self, value):
        """Set new production input1."""
        self._input1 = self._validate_input(value)

    @property
    def input2(self):
        """
        Class describing a heterogenous production input.

        :getter: Return production input2.
        :setter: Set new production input2.
        :type: inputs.Input

        """
        return self._input2

    @input2.setter
    def input2(self, value):
        """Set new production input2."""
        self._input2 = self._validate_input(value)

    @staticmethod
    def _validate_assortativity(value):
        """Validates the matching assortativity."""
        valid_assortativities = ['positive', 'negative']
        if not isinstance(value, str):
            mesg = "Attribute 'assortativity' must have type str, not {}."
            raise AttributeError(mesg.format(value.__class__))
        elif value not in valid_assortativities:
            mesg = "Attribute 'assortativity' must be in {}."
            raise AttributeError(mesg.format(valid_assortativities))
        else:
            return value

    @staticmethod
    def _validate_input(value):
        """Validates the input1 and input2 attributes."""
        if not isinstance(value, inputs.Input):
            mesg = ("Attributes 'input1' and 'input2' must have " +
                    "type inputs.Input, not {}.")
            raise AttributeError(mesg.format(value.__class__))
        else:
            return value

    @staticmethod
    def _validate_F_params(params):
        """Validates the dictionary of model parameters."""
        if not isinstance(params, dict):
            mesg = "Attribute 'params' must have type dict, not {}."
            raise AttributeError(mesg.format(params.__class__))
        else:
            return params

    def _validate_production_function(self, F):
        """Validates the production function attribute."""
        if not isinstance(F, sym.Basic):
            mesg = "Attribute 'F' must have type sympy.Basic, not {}."
            raise AttributeError(mesg.format(F.__class__))
        elif not set(self._required_symbols) < F.atoms():
            mesg = "Attribute 'F' must be an expression of r and l."
            raise AttributeError(mesg)
        elif not {self.input1.var, self.input2.var} < F.atoms():
            mesg = ("Attribute 'F' must be an expression of input1.var and " +
                    "input2.var variables.")
            raise AttributeError(mesg)
        else:
            return F
