"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import numpy as np
import matplotlib.pyplot as plt
from os import path

plot_styles = {
    'gam_GB': ['Growth Rate [GB]', 'wavenumber', r'growth rate [$\sqrt{T_e/mi}/a$]'],
    'gam_SI': ['Growth Rate [SI]', 'wavenumber', r'growth rate [$\sqrt{T_e/mi}/a$]'],
    'ome_GB': ['Frequencies [GB]', 'wavenumber', r'frequency [?]'],
    'ome_SI': ['Frequencies [SI]', 'wavenumber', r'frequency [$s^-1$]'],

    'ief_GB': ['Ion Heat Conductivity [GB]', 'ions', r'heat conductivity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'ief_SI': ['Ion Heat Flux [SI]', 'ions', r'heat flux [$W/m^2$]'],
    'eef_GB': ['Electron Heat Conductivity [GB]', 'electrons', r'heat conductivity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'eef_SI': ['Electron Heat Flux [SI]', 'electrons', r'heat flux [$W/m^2$]'],
    'eefETG_SI': ['Electron Scale Heat Flux [SI]', 'electrons', r'heat flux [$W/m^2$]'],
    'ipf_GB': ['Ion Particle Diffusivity [GB]', 'ions', r'particle diffusifity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'ipf_SI': ['Ion Particle Flux [SI]', 'ions', r'particle flux [$m^-2 s^-1$]'],
    'epf_GB': ['Electron Particle Diffusivity [GB]', 'electrons', r'particle diffusifity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'epf_SI': ['Electron Particle Flux [GB]', 'electrons', r'particle flux [$m^-2 s^-1$]'],
    'epfETG_SI': ['Electron Scale Particle Flux [GB]', 'electrons', r'particle flux [$m^-2 s^-1$]'],
    'ivf_GB': ['Ion Momentum Diffusivity [GB]', 'ions', r'momentum diffusifity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'ivf_SI': ['Ion Momentum Flux [SI]', 'ions', r'momentum flux [$N s m^-2 s^-1$]'],
    'evf_GB': ['Electron Momentum Diffusivity [GB]', 'electrons', r'momentum diffusifity [$\sqrt{mi}T_e^{1.5}/(q_e^2B^2a)$]'],
    'ivf_SI': ['Electron Momentum Flux [SI]', 'electrons', r'momentum flux [$N s m^-2 s^-1$]'],

}

prims = {
    'gam': ['growth rate', 'SI', 'GB'],
    'ome': ['frequencies', 'SI', 'GB'],
    'ef': ['heat', 'conductivity', 'flux'],
    'efETG': ['heat', 'conductivity', 'flux'],
    'pf': ['particle', 'diffusivity', 'flux'],
    'pfETG': ['particle', 'diffusivity', 'flux'],
    'vf': ['momentum', 'diffusivity', 'flux'],
    'df': ['', 'diffusivity', None],
    'vt': ['particle', 'thermopinch', None],
    'vr': ['particle', 'rotodiffusion pinch', None],
    'vc': ['particle', 'compressebility pinch', None],
    'chie': ['heat', 'conductivity', None],
    'ven': ['heat', 'thermopinch', None],
    'ver': ['heat', 'rotodiffusion pinch', None],
    'vec': ['heat', 'compressebility pinch', None]}


file_list = []
for file_dir in file_list:
    __, temp = path.split(file_dir)
    name, __ = path.splitext(temp)
    base, __, unit = name.partition("_")
    if unit == "SI" and not (base.startswith("e") or base.startswith("i")) \
        and not (base == "gam" or base == "ome"):
        base = base[-1] + base[:-1]

    if base == "gam" or base == "ome":
        prim = base
        title = prims[prim][0] + " "
        if unit == "SI":
            title += prims[prim][1]
        elif unit == "GB":
            title += prims[prim][2]
        plotWrapper(np.array(listify(file_dir)), [title, 'w', "label"])
    elif not unit == "SI" and not unit == "GB":
        pass
    else:
        prim = base[1:]
        if base.startswith('i'):
            title = 'Ion '
        elif base.startswith('e'):
            title = 'Electron '
        title += prims[prim][0] + ' '
        if unit == "SI":
            title += prims[prim][1]
        elif unit == "GB":
            title += prims[prim][2]
        plotWrapper(np.array(listify(file_dir)), [title, base, "label"])
    output[name] = np.array(listify(file_dir))
