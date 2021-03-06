"""
Copyright Dutch Institute for Fundamental Energy Research (2016-2017)
Contributors: Karel van de Plassche (karelvandeplassche@gmail.com)
License: CeCILL v2.1
"""
from qualikiz_tools.qualikiz_io.qualikizrun import QuaLiKizRun, QuaLiKizBatch
from warnings import warn

class Run(QuaLiKizRun):
    def to_batch_string(self, *args, **kwargs):
        raise NotImplementedError('Run to_batch_string not implemented yet')

    @classmethod
    def from_batch_string(cls, *args, **kwargs):
        raise NotImplementedError('Run from_batch_string not implemented yet')

    @classmethod
    def from_dir(cls, dir, *args, **kwargs):
        warn('Specialized from_dir method not defined')
        return super().from_dir(dir, *args, **kwargs)


    def launch(self, *args, **kwargs):
        raise NotImplementedError('Run launch not implemented yet')

class Batch(QuaLiKizBatch):
    run_class = None
    def to_batch_file(self, path, *args, **kwargs):
        raise NotImplementedError('Batch to_file not implemented yet')

    @classmethod
    def from_batch_file(cls, path, *args, **kwargs):
        raise NotImplementedError('Batch from_file not implemented yet')

    def launch(self, *args, **kwargs):
        raise NotImplementedError('Batch launch not implemented yet')

