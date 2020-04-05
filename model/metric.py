import torch
import numpy as np

def _preprocess(output, target):
    output = output.detach().cpu()
    output = output.argmax(dim=1)
    output = output.to(torch.uint8)

    target = target.to(torch.uint8)
    target = target.cpu()

    return output, target


def _thresholded(val):
    # This is equal to comparing with thresolds
    # The minimum value of a correct metric is 0.5, the following will measure how correct a corect
    # segmentation is (segmentation with metric > 0.5).
    return torch.clamp(20 * (val - 0.5), 0, 10).ceil() / 10

def classwise_iou(output, target, n_class=21):
    SMOOTH = 1e-10

    output, target = _preprocess(output, target)
    class_wise = torch.zeros(n_class)
    class_wise[0] = np.nan
    for cl in range(1, n_class):
        intersection = ((target == cl) & (output == cl)).sum().float()
        union = ((target == cl) | (output == cl)).sum().float()

        if union.item() == 0: # A union of zero should be ignored
            class_wise[cl] = float('NaN')
        else:
            iou = intersection / (union + 1e-10)
            class_wise[cl] = iou
    return class_wise

def classwise_dice(output, target, n_class=21):
    SMOOTH = 1e-10

    output, target = _preprocess(output, target)
    class_wise = torch.zeros(n_class)
    class_wise[0] = np.nan
    for cl in range(1, n_class):
        intersection = ((target == cl) & (output == cl)).sum().float()
        total = ((target == cl).sum() + (output == cl).sum()).float()

        if total.item() == 0: # A union of zero should be ignored
            class_wise[cl] = float('NaN')
        else:
            dice = (intersection * 2) / (total + 1e-10)
            class_wise[cl] = dice
    return class_wise


def mean_iou(output, target, nclass=21):
    """Mean Intersection of Union
    Args:
        predict: input 4D tensor
        target: label 3D tensor
        nclass: number of categories (int)
    """
    SMOOTH = 1e-10
    predict = output.argmax(dim=1)
    mini = 1
    maxi = nclass
    nbins = nclass
    predict = predict.cpu().numpy().astype('int64') + 1
    target = target.cpu().numpy().astype('int64') + 1

    predict = predict * (target > 0).astype(predict.dtype)
    intersection = predict * (predict == target)
    # areas of intersection and union
    area_inter, _ = np.histogram(intersection, bins=nbins, range=(mini, maxi))
    area_pred, _ = np.histogram(predict, bins=nbins, range=(mini, maxi))
    area_lab, _ = np.histogram(target, bins=nbins, range=(mini, maxi))
    area_union = area_pred + area_lab - area_inter

    assert (area_inter <= area_union).all(), \
        "Intersection area should be smaller than Union area"
        
    IoU = 1.0 * area_inter / (np.spacing(1) + area_union)
    mIoU = IoU.mean()
    return mIoU


def meanIoU(output, target, n_class=21):
    classwise = classwise_iou(output, target, n_class)

    # thresholded = _thresholded(classwise)
    mean = np.nanmean(classwise)
    return 0 if np.isnan(mean) else mean


def meanDice(output, target, n_class=21):
    classwise = classwise_dice(output, target, n_class)

    # thresholded = _thresholded(classwise)
    mean = np.nanmean(classwise)
    return 0 if np.isnan(mean) else mean
