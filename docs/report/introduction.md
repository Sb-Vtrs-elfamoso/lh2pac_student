# Introduction
## Context
During ModIA formation, Meta-modelization course aims to teach students about surrogate models usages and challenges. Thus, this project supervized by [Matthias De Lozzo](matthias.delozzo@irt-saintexupery.com) deals with models and surrogate models of hygrogen powered turbofan airplanes. In fact, hydrogen is a candidate to replace kerosene for future airplanes because it does not emit carbon dioxide when burning,
as described in the  [The Airbus' ZEROe project](https://www.airbus.com/en/innovation/low-carbon-aviation/hydrogen/zeroe).

The objective of this study is to evaluate the impact of the use of liquid hydrogen in place of kerosene on the design and performances of a turbofan airplane.

For more informations about Hydrogen powered aircrafts, please refer to [use case introduction](../presentation/use_case.md)

!!! note

    This study case is kindly provided
    by [Thierry Druot](https://cv.archives-ouvertes.fr/thierry-druot>),
    Pre-Project Research Engineer at [Airbus](https://www.airbus.com/>),
    seconded to [ENAC](https://www.enac.fr/en).
    The authors of this practice are very grateful to him.
    Thanks, Thierry!

## Model
The problem is to find the “best” hydrogen powered airplane design
that satisfies the same operational constraints as the kerosene A320
(except for the range). The existing know how in terms of airplane design has shown that the Maximum Take-Off Weight `mtow` of the airplane is a good criterion to optimize a design.

We can summarize the design problem as follows :

> Find the values of the **design parameters** 
> that minimize the **criterion MTOW**
> whilst satisfying **operational constraints**.

The **design parameters** $x$ are aircraft design modifications of specifications. They are :

- the engine maximum thrust  (100 kN ≤ thrust ≤ 150 kN, default: 125 kN),
- the engine bypass ratio  (BPR)  (5 ≤ BPR ≤ 12, default: 8.5),
- the wing area  (120 m² ≤ area ≤ 200 m², default: 160 m²),
- the wing aspect ratio  (7 ≤ ar ≤ 12, default: 9.5).

The **operational constraints** $u$ ensure that hydrogen airplane achieves A320 performances. They are :

- the take off field length (TOFL ≤ 2200 m),
- the approach speed (VAPP ≤ 137 kt),
- the vertical speed MCL rating  (300 ft/min ≤ VZ_MCL),
- the vertical MCR rating  (0 ft/min ≤ VZ_MCR),
- the one engine inoperative climb path  (1.1% ≤ OEI_PATH),
- the time To climb to cruise altitude  (TTC ≤ 25 min),
- the fuselage aspect Ratio  (FAR ≤ 13.4).

In addition to this,
several **technological parameters** need to be taken into account. They represent technological developements which could be hypothetically improved  for hydrogen aircrafts production :

1. the tank gravimetric index = 0.3,
   with uncertainty: Triangular(0.25, 0.3, 0.305),
2. the tank volumetric index = 0.845,
   with uncertainty: Triangular(0.8, 0.845, 085),
3. the aerodynamic efficiency factor = 1.,
   with uncertainty: Triangular(0.99, 1., 1.03),
4. the propulsion efficiency factor = 1.,
   with uncertainty: Triangular(0.99, 1., 1.03),
5. the structure efficiency factor = 1.,
   with uncertainty: Triangular(0.99, 1., 1.03),

where Triangular($a$, $b$, $c$) represents
the [triangular distribution](https://en.wikipedia.org/wiki/Triangular_distribution)
with lower limit $a$, mode $d$ and upper limit $c$: [Triangular distribution](../images/use_case/triangular.png)

[Next : Problem 1, Surrogate modeling and Optimization](../report/part1.md)
