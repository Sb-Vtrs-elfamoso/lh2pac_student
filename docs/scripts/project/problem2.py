"""
Problem 2 : Uncertainty quantification
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
from gemseo.algos.design_space import DesignSpace
from gemseo.algos.parameter_space import ParameterSpace
from gemseo.mlearning.quality_measures.r2_measure import R2Measure
from gemseo.mlearning.quality_measures.rmse_measure import RMSEMeasure
from gemseo_mlearning.api import sample_discipline


from lh2pac.marilib.utils import unit

configure_logger()
# %%

# ## Airplane initialization
# First, we instantiate the discipline:
discipline = H2TurboFan()
# %%
# Then,
# we can have a look at its input names:
print('input data names : ')
print(discipline.get_input_data_names())
# %%

output_parameters = discipline.get_output_data_names()
print('output params :')
print(output_parameters)
# %%

# and default input values:
print('default inputs :')
print(discipline.default_inputs)
# %%

# and execute the discipline with these values:
discipline.execute()
# %%

# We can print the aircraft data:
aircraft_data = get_aircraft_data(discipline)

# aircraft data 
print('aircraft data : ')
print(aircraft_data)
# %%

# and draw the aircraft:
draw_aircraft(discipline, "The default A/C")


# %%
class MyUncertainSpace(ParameterSpace):
    def __init__(self):
        super().__init__()
        self.add_random_variable("tgi", "SPTriangularDistribution", minimum=0.25,mode=0.3, maximum=0.305)
        self.add_random_variable("tvi", "SPTriangularDistribution", minimum=0.8,mode=0.845, maximum=0.85)
        self.add_random_variable("sfc", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("mass", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        self.add_random_variable("drag", "SPTriangularDistribution", minimum=0.99,mode=1.0, maximum=1.03)
        
# %%
uncertain_space = MyUncertainSpace()
print(uncertain_space)
# %%
dataset = sample_discipline(discipline, uncertain_space, ['mtow'], "OT_MONTE_CARLO", 100)

# %%

from gemseo.uncertainty import create_statistics
statistics = create_statistics(dataset)
mean = statistics.compute_mean()
variance = statistics.compute_variance()
names = ["mtow","tgi","tvi","sfc","mass","drag"]
for name in names:
    print(name, mean[name][0], variance[name][0])
# %%
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 3,figsize = (15,10))
for i,(ax, name) in enumerate(zip(axes.flatten(), names)):
    ax.hist(dataset.get_view(variable_names=name),bins=20,)
    ax.set_title(name)
plt.show()
# %%
## compute Sobol indices
from gemseo.uncertainty.sensitivity.sobol.analysis import SobolAnalysis

sobol = SobolAnalysis([discipline],uncertain_space,100)
sobol.compute_indices()
# %%
import pprint
pprint.pprint(sobol.first_order_indices)
pprint.pprint(sobol.total_order_indices)
# %%
sobol.plot("mtow",save=False,show=True)
# %%
## sobol for surrogate model 
dataset_surro = sample_discipline(
    discipline,
    uncertain_space,
    ["mtow"],
    "OT_OPT_LHS",
    30
)
    # %%
regressors = [
    "GaussianProcessRegressor",
    "GradientBoostingRegressor",
    "LinearRegressor",
    "MLPRegressor",
    "MOERegressor",
    "OTGaussianProcessRegressor",
    "PCERegressor",
    "PolynomialRegressor",
    "RBFRegressor",
    "RandomForestRegressor",
    "RegressorChain",
    "SVMRegressor",
    "TPSRegressor"
]
surrogate_discipline = create_surrogate("RBFRegressor",dataset_surro)
print(surrogate_discipline)
# %%
sobol = SobolAnalysis([surrogate_discipline],uncertain_space,10000)
sobol.compute_indices()
# %%
import pprint
pprint.pprint(sobol.first_order_indices)
pprint.pprint(sobol.total_order_indices)
# %%
sobol.plot("mtow",save=False,show=True)
# %%
## Morris Analysis 
from gemseo.uncertainty.sensitivity.morris.analysis import MorrisAnalysis
morris_analysis = MorrisAnalysis([discipline], uncertain_space, 100)
morris_analysis.compute_indices() 
# %%
surrogate_morris_analysis = MorrisAnalysis([surrogate_discipline],uncertain_space,100)
surrogate_morris_analysis.compute_indices() 

# %%
morris_analysis.plot("mtow",save=False,show=True)

# %%
surrogate_morris_analysis.plot("mtow",save=False,show=True)
# %%
