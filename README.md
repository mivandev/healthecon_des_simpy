# Simple health economic DES model with Python

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mivandev/healthecon_des_simpy/blob/main/he_model_oo.ipynb)

A very simple model to serve as an exploration of creating health economic Discrete-Event Simulation (DES) models in Python using SimPy library. The clinical context of the model is as follows:
* During a cycle of treatment, patients can either die (p = 0.15) or experience a full cycle of treatment without any other events occurring.
* Patients can receive up to five cycles of treatment.
* A full cycle causes a longer delay or timeout compared to dying during a cycle. These timeouts are drawn from a Gamma distribution.
* After surviving the maximum number of treatment cycles, patients will enter a follow up phase, in which patients can also die.

The health economic context is as follows:
* Each cycle of treatment incurs 5000 euro initially and 250 euro per day.
* Followup costs 3500 euro per patient as a lumpsum.
* Health-related quality of life (QoL) in the treatment phase is 0.7 as expressed over the duration of one year.
* QoL in the followup phase is 0.8 as expressed over the duration of one year.

Furthermore, all patients are simulated at `t = 0`, so the interarrival time = 0. Note that the model currently only represents one comparator. So for an actual cost-effectiveness analysis, another comparator must be added, but this is very straightforward.

Three classes are created for the model: 1) a class `g` contains all constants, 2) a `Patient` class in which attributes of patients are set and 3) a `Model` class containing the model structure and Patient Generator method. The model is run by creating an instance of `Model` and subsequently executing the `run()` method of that `Model` instance. To accomodate the need to conduct multiple runs, this is performed in a for loop.