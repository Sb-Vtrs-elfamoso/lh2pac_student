"""
Surrogate modeling
"""
# %%

from numpy import array
import pickle
from pathlib import Path

from lh2pac.gemseo.discipline import H2TurboFan
from lh2pac.gemseo.utils import draw_aircraft
from lh2pac.gemseo.utils import get_aircraft_data

from gemseo import configure_logger
from gemseo import create_scenario
from gemseo import create_surrogate
from gemseo import import_discipline
from gemseo import configure
from gemseo.algos.design_space import DesignSpace
from gemseo.mlearning.quality_measures.r2_measure import R2Measure
from gemseo.mlearning.quality_measures.rmse_measure import RMSEMeasure
from gemseo.uncertainty.sensitivity.sobol.analysis import SobolAnalysis
from lh2pac.marilib.utils import unit

#%%
# ## Désactivations des fonctionnalités non utlisées de Gemseo

#configure(activate_discipline_counters=False, activate_function_counters=False, activate_progress_bar=True, activate_discipline_cache=True, check_input_data=False, check_output_data=False, check_desvars_bounds=False)
# %%
# ## Airplane initialization
# First, we instantiate the discipline:
discipline = H2TurboFan()

# %%
# Then,
# we can have a look at its input names:
discipline.get_input_data_names()

# %%
# output names:
output_parameters = discipline.get_output_data_names()
print(output_parameters)

# %%
# and default input values:
discipline.default_inputs

# %%
# and execute the discipline with these values:
discipline.execute()

# %%
# We can print the aircraft data:
aircraft_data = get_aircraft_data(discipline)
print(aircraft_data)

# %%
# and draw the aircraft:
draw_aircraft(discipline, "The default A/C")

# %%
# ## Design of experiment
# we activate the logger.
configure_logger()

# we create the design space for design parameters $x$ :
class MyDesignSpace(DesignSpace):
    def __init__(self):
        super().__init__(name="foo")
        self.add_variable("thrust", l_b=unit.N_kN(100), u_b=unit.N_kN(150))
        self.add_variable("bpr", l_b=5, u_b=12)
        self.add_variable("area", l_b=120, u_b=200)
        self.add_variable("aspect_ratio", l_b=7, u_b=12)

design_space = MyDesignSpace()


# %%
# Thirdly,
# we create a `DOEScenario` from this discipline and this design space:
disciplines = [discipline]
scenario = create_scenario(
    disciplines, "DisciplinaryOpt", output_parameters[0], design_space, scenario_type="DOE"
)
for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter)

# %%
# Now,
# we can sample the discipline to get 100 evaluations of the airplane parameters :
scenario.execute({"algo": "OT_OPT_LHS", "n_samples": 100})

# %%
# Lastly,
# we can export the result to an `IODataset`
# which is a subclass of `Dataset`,
# which is a subclass of `pandas.DataFrame`:
dataset = scenario.to_dataset(opt_naming=False)
dataset

# %%
# ## Surrogate modeling
# before creating a surrogate discipline:
surrogate_discipline = create_surrogate("RBFRegressor", dataset)

# %%
# and using it for prediction:
surrogate_discipline.execute({"x": array([1.0])})
surrogate_discipline.cache.last_entry

# %%
# This surrogate discipline can be used in a scenario.
# The underlying regression model can also be assessed,
# with the R2 measure for instance:
r2 = R2Measure(surrogate_discipline.regression_model, True)
print(r2.compute_learning_measure())
print(r2.compute_cross_validation_measure())

# %%
# or with the root mean squared error:
rmse = RMSEMeasure(surrogate_discipline.regression_model, True)
print(rmse.compute_learning_measure())
print(rmse.compute_cross_validation_measure())

# %% 
# Saving model and testing
with Path("my_surrogate.pkl").open("wb") as f:
    pickle.dump(surrogate_discipline, f)

surrogate_discipline = import_discipline("my_surrogate.pkl")
surrogate_discipline.execute({"x": array([1.0])})
surrogate_discipline.get_output_data()

# %%
# Thirdly,
# we put these elements together in a scenario
# to minimize the Rosenbrock function
# under the constraint that the distance
# between the design point and the solution of the unconstrained problem
# is greater or equal to 1.
scenario_surrogate = create_scenario([surrogate_discipline], "DisciplinaryOpt", output_parameters[0], design_space)
for parameter in  output_parameters[1:] :
    scenario.add_observable(parameter)

scenario_surrogate.add_constraint("tofl", constraint_type="ineq", positive=False, value=2200)
scenario_surrogate.add_constraint("vapp", constraint_type="ineq", positive=False, value=unit.mps_kt(137))
scenario_surrogate.add_constraint("vz_mcl", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(300))
scenario_surrogate.add_constraint("vz_mcr", constraint_type="ineq", positive=True, value=unit.mps_ftpmin(0))
scenario_surrogate.add_constraint("oei_path", constraint_type="ineq", positive=True, value=0.011)
scenario_surrogate.add_constraint("ttc", constraint_type="ineq", positive=False, value=unit.s_min(25))
scenario_surrogate.add_constraint("far", constraint_type="ineq", positive=False, value=13.4)

# %%
# before executing it with a gradient-free optimizer:
scenario_surrogate.execute({"algo": "NLOPT_COBYLA", "max_iter": 1000})

# %%
# Lastly,
# we can plot the optimization history:
scenario_surrogate.post_process("OptHistoryView", save=False, show=True)

# %%
# We can print the aircraft data:
print(surrogate_discipline.get_input_data())

# %%
# and draw the aircraft:
draw_aircraft(surrogate_discipline.get_input_data(), "The optimized A/C")

