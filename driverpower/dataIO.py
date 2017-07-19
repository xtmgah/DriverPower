""" Data input and output module for DriverPower.

Input file types: X (tsv), y (tsv), functional scores (tsv), models (pkl)

"""
import logging
import pickle
import sys
import os
import pkg_resources
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.externals import joblib
from statsmodels.iolib import smpickle

logger = logging.getLogger('IO')


def read_feature(path, use_features=None):
    """Read X (features) table in TSV format (or compressed).
    
    X must contain a column named 'binID' (key) and other columns will be treated as features.
    
    Args:
        path (str): Path to the file.
        use_features (list): List of features to load.

    Returns:
        pd.df: A panda DF indexed by binID.

    """
    if use_features:
        X = pd.read_csv(path, sep='\t', header=0, index_col='binID',
                        usecols=['binID'] + use_features)
    else:
        X = pd.read_csv(path, sep='\t', header=0, index_col='binID')
    # sanity check
    assert len(X.index.values) == len(X.index.unique()), "binID in feature table is not unique."
    na_count = X.isnull().sum()
    if na_count.sum() > 0:
        na_names = na_count.index.values[np.where(na_count>0)]
        logger.warning('NA values found in features [{}]'.format(', '.join(na_names)))
        logger.warning('Fill NA with 0')
        X.fillna(0, inplace=True)
    logger.info('Successfully load {} features for {} bins'.format(X.shape[1], X.shape[0]))
    return X


def read_response(path):
    """Read y (response) table in TSV format.
    
    y should have exactly four columns: binID, length, nMut, nSample, N
    
    Args:
        path (str): Path to the file.
    
    Returns:
        pd.df: A panda DF indexed by binID.
        
    """
    y = pd.read_csv(path, sep='\t', header=0, index_col='binID',
                    usecols=['binID', 'length', 'nMut', 'nSample', 'N'])
    # sanity check
    assert len(y.index.values) == len(y.index.unique()), "binID in response table is not unique."
    return y


def read_fs(path, fs_cut):
    """Read functional scores table in TSV format.
    
    func_score must contain a column named 'binID' (key) and other columns will be treated as scores (one per column).
    
    Args:
        path (str): Path to the file.
        fs_cut (dict): Keys are functional score names.
    
    Returns:
        pd.df: A panda DF indexed by binID
         
    """
    fs = pd.read_csv(path, sep='\t', header=0, index_col='binID',
                     usecols=['binID'] + list(fs_cut.keys()))
    # sanity check
    assert len(fs.index.values) == len(fs.index.unique()), "binID in functional score table is not unique."
    return fs


def read_scaler(path):
    """ Load the scaler from disk.

    Args:
        path (str): path to the pkl.

    Returns:
        RobustScaler.

    """
    scaler = joblib.load(path)
    return scaler



def save_scaler(scaler, project_name, out_dir):
    """ Dump the scaler to disk.

    Args:
        scaler (RobustScaler):
        project_name (str): name of the project, prefix of the output file.
        out_dir (str): output directory.

    Returns:
        None.

    """
    path = os.path.join(out_dir, project_name+'.feature_scaler.pkl')
    joblib.dump(scaler, path)
    return


def read_fi(path, cutoff=0.5):
    """Read feature importance table in TSV format.

    Feature importance table must contain two columns: name and importance

    Args:
        path (str): path to the file.
        cutoff (float): cutoff of feature selection.

    Returns:
        list: useful features. Return None if path is None.

    """
    if path:
        fi = pd.read_csv(path, sep='\t', header=0, index_col='name',
                         usecols=['name', 'importance'])
        assert len(fi.index.values) == len(fi.index.unique()), \
            "Feature name in feature importance table is not unique."
        keep = (fi.importance >= cutoff).values
        return fi.index.values[keep].tolist()
    else:
        return None


def save_fi(fi_scores, feature_names, project_name, out_dir):
    """ Save feature importance results to disk
    
    Args:
        fi_scores (np.array): array of feature importance scores.
        feature_names (np.array): array of feature names.
        project_name (str): name of the project, prefix of the output file.
        out_dir (str): output directory. 

    Returns:
        pd.DF: feature importance table
        
    """
    res = pd.DataFrame({'name':feature_names, 'importance':fi_scores})
    path = os.path.join(out_dir, project_name+'.feature_importance.tsv')
    res.to_csv(path, sep='\t')
    return res


def read_glm(path):
    """ Load the saved GLM model

    Args:
        path (str): path to the model

    Returns:

    """
    model = smpickle.load_pickle(path)
    return model


def save_glm(model, project_name, out_dir):
    """ Save the trained GLM model

    When saving the model, all training data are removed to save space.

    Args:
        model (sm GLMResultsWrapper): trained GLM model
        project_name (str): name of the project, prefix of the output file.
        out_dir (str): output directory.

    Returns:
        None.

    """
    path = os.path.join(out_dir, project_name+'.GLM.pkl')
    model.save(path, remove_data=True)
    return


def read_param(path=None):
    """ Load the parameter for xgboost.

    Args:
        path: path to the pkl file. None for default.

    Returns:
        dict: parameter dict.
    """
    # use default if path is None
    path = path if path else pkg_resources.resource_filename(__name__, 'xgb_param.pkl')
    with open(path, 'rb') as f:
        param = pickle.load(f)
    return param


def save_gbm(bst, k, project_name, out_dir):
    path = os.path.join(out_dir, '{}.GBM.model.fold{}'.format(project_name, k))
    bst.save_model(path)
    return


def load_gbm(k, project_name, out_dir):
    path = os.path.join(out_dir, '{}.GBM.model.fold{}'.format(project_name, k))
    bst = xgb.Booster(model_file=path)
    return bst


def read_model_info(path):
    with open(path, 'rb') as f:
        model_info = pickle.load(f)
    return model_info


def save_model_info(model_info, out_dir, project_name):
    path = os.path.join(out_dir, project_name+'.model_info.pkl')
    with open(path, 'wb') as f:
        pickle.dump(model_info, f)


def save_result(y):
    pass
