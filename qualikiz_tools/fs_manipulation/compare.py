"""
Copyright Dutch Institute for Fundamental Energy Research (2016)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
import os
import re
import warnings
import numpy as np


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def diff_filelist(folder1, folder2):
    folder1_files = [file for file in os.listdir(folder1) if
                     os.path.isfile(os.path.join(folder1, file))]
    folder2_files = [file for file in os.listdir(folder2) if
                     os.path.isfile(os.path.join(folder2, file))]
    folder1_files = sorted(folder1_files, key=natural_keys)
    folder2_files = sorted(folder2_files, key=natural_keys)

    not_in_1 = [file for file in folder2_files if file not in folder1_files]
    not_in_2 = [file for file in folder1_files if file not in folder2_files]
    in_both = [file for file in folder1_files if file in folder2_files]
    return (not_in_1, not_in_2, in_both)


def ascii_to_np(filepath):
    if filepath.endswith('.dat'):
        with open(filepath, 'rb') as file:
            try:
                nparr = np.loadtxt(file)
            except ValueError as error:
                l_ = error.args[0].find('\'')
                r_ = error.args[0].rfind('\'')
                errorstr = error.args[0][l_+1:r_].encode('utf-8')
                file.seek(0)
                newlines = []
                for line in file:
                    newlines.append(line.replace(errorstr, b'NaN'))
                nparr = np.loadtxt(newlines)
        return nparr
    else:
        warnings.warn('\'' + filepath + '\' is not ascii, ignoring..')


def bin_to_np(filepath):
    if filepath.endswith('.bin'):
        with open(filepath, 'rb') as file:
            nparr = np.fromfile(file)
        return nparr
    else:
        warnings.warn('\'' + filepath + '\' is not binary, ignoring..')


def diff(folder1, folder2, to_np, rtol=1e-2):
    not_in_1, not_in_2, in_both = diff_filelist(folder1, folder2)
    different = False
    if len(not_in_1) > 0:
        print('Files not in \'' + folder1 + '\':')
        for filename in not_in_1:
            print(os.path.basename(filename))
            print(to_np(os.path.join(folder2, filename)))
        different = True
    if len(not_in_2) > 0:
        print('Files not in \'' + folder2 + '\':')
        for filename in not_in_2:
            print(os.path.basename(filename))
            print(to_np(os.path.join(folder1, filename)))
        different = True

    print('Files in both:')
    for filename in in_both:
        arr1 = to_np(os.path.join(folder1, filename))
        arr2 = to_np(os.path.join(folder2, filename))
        if arr1 is not None and arr2 is not None:
            try:
                isclose = np.allclose(arr1, arr2, rtol=rtol, equal_nan=True)
            except ValueError:
                isclose = False
            if not isclose or not arr1.shape == arr2.shape:
                print(os.path.basename(filename))
                print(arr1)
                print(arr2)
                different = True
    return different


def compare_runs(folder1, folder2):
    print('comparing \'debug\'')
    different = diff(os.path.join(folder1, 'debug'),
                     os.path.join(folder2, 'debug'), ascii_to_np)
    print('comparing \'input\'')
    different = diff(os.path.join(folder1, 'input'),
                     os.path.join(folder2, 'input'), bin_to_np)
    print('comparing \'output\'')
    different |= diff(os.path.join(folder1, 'output'),
                      os.path.join(folder2, 'output'), ascii_to_np)
    print('comparing \'primitive\'')
    different |= diff(os.path.join(folder1, 'output/primitive'),
                      os.path.join(folder2, 'output/primitive'), ascii_to_np)
    if different:
        print('different')
    else:
        print('identical')
    return different
