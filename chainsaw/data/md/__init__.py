import  pkgutil

loader = pkgutil.find_loader('mdtraj')

if loader is not None:
    from .feature_reader import FeatureReader
    from .featurization.featurizer import MDFeaturizer, CustomFeature
