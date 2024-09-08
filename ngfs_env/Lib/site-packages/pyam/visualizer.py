import numpy as np
import pandas as pd

import pycollocation


class Visualizer(pycollocation.Visualizer):
    """Class for visualizing various functions of the solution to the model."""

    __complementarities = ['Fxy', 'Fxl', 'Fxr', 'Fyl', 'Fyr', 'Flr']

    __partials = ['F', 'Fx', 'Fy', 'Fl', 'Fr']

    __solution = None

    @property
    def _combined_solution_functionals(self):
        """Dictionary of functions evaluated along the model solution."""
        tmp = {}
        tmp.update(self._complementarities)
        tmp.update(self._partials)
        tmp.update(self._factor_payments)
        return tmp

    @property
    def _complementarities(self):
        """Dictionary mapping a complementarity to a callable function."""
        tmp = {}
        for complementarity in self.__complementarities:
            expr = eval("self.solver.problem." + complementarity)
            tmp[complementarity] = self.solver.problem._lambdify_factory(expr.subs(self.solver.problem._subs))

        return tmp

    @property
    def _factor_payments(self):
        """Dictionary mapping a factor payment to a callable function."""
        tmp = {}
        for payment in ["factor_payment_1", "factor_payment_2"]:
            expr = eval("self.solver.problem." + payment)
            tmp[payment] = self.solver.problem._lambdify_factory(expr)

        return tmp

    @property
    def _partials(self):
        """Dictionary mapping a partial derivative to a callable function."""
        tmp = {}
        for partial in self.__partials:
            expr = eval("self.solver.problem." + partial)
            tmp[partial] = self.solver.problem._lambdify_factory(expr.subs(self.solver.problem._subs))

        return tmp

    @property
    def _solution(self):
        """Return the solution stored as a dict of NumPy arrays."""
        if self.__solution is None:
            tmp = super(Visualizer, self)._solution

            for key, function in self._combined_solution_functionals.items():
                values = function(self.interpolation_knots,
                                  tmp['mu'].values,
                                  tmp['theta'].values,
                                  *self.solver.problem.params.values())
                tmp[key] = pd.Series(values, index=self.interpolation_knots)

            self.__solution = tmp

        return self.__solution

    def _theta_frequency(self):
        """Compute the frequency (i.e, measure) of firm size."""
        tmp_df = self.solution.sort('theta', ascending=True, inplace=False)
        input1_freq = self.solver.problem.input1.evaluate_pdf(tmp_df.index.values)
        theta_frequency = input1_freq / tmp_df.theta
        return theta_frequency

    @staticmethod
    def compute_cdf(pdf):
        """Compute the cumulative distribution function (cdf) given a pdf."""
        values = np.array([np.trapz(pdf.iloc[:x], pdf.index[:x]) for x in range(pdf.size)])
        cdf = pd.Series(values, index=pdf.index.values)
        return cdf

    @staticmethod
    def compute_sf(cdf):
        """Compute the survival function (sf) given a cdf."""
        sf = 1 - cdf
        return sf

    def compute_pdf(self, variable, normalize=True):
        """Compute the probability density function (pdf) for some variable."""
        tmp_df = self.solution.sort(variable, ascending=True, inplace=False)
        tmp_df['theta_frequency'] = self._theta_frequency()

        if normalize:
            area = np.trapz(tmp_df.theta_frequency, tmp_df[variable])  # normalize by area!
            density = tmp_df.theta_frequency / area
            pdf = pd.Series(density.values, index=tmp_df[variable].values)
        else:
            pdf = pd.Series(tmp_df.theta_frequency.values, index=tmp_df[variable].values)

        return pdf
