import pickle
import random

import cv2 as cv
import torch
import torch.nn.functional as F

from config import pickle_file, im_size
from data_gen import pad_collate
from utils import ensure_folder

if __name__ == '__main__':
    checkpoint = 'BEST_checkpoint.tar'
    checkpoint = torch.load(checkpoint)
    model = checkpoint['model']
    model.eval()

    with open(pickle_file, 'rb') as file:
        data = pickle.load(file)

    VOCAB = data['VOCAB']
    IVOCAB = data['IVOCAB']
    val = data['val']
    image_ids_val, questions_val, answers_val = val
    prefix = 'data/val2014/COCO_val2014_0000'

    chosen_samples = range(len(val))
    _ids = random.sample(chosen_samples, 10)

    _pred_ids = []
    questions = []
    targets = []
    ensure_folder('images')

    batch = []

    for i, index in _ids:
        image_id = int(image_ids_val[index])
        image_id = '{:08d}'.format(image_id)
        filename = prefix + image_id + '.jpg'
        img = cv.imread(filename)
        img = cv.resize(img, (im_size, im_size))
        filename = 'images/{}_img.png'.format(i)
        cv.imwrite(filename, img)

        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        img = img.transpose(2, 0, 1)
        img = (img - 127.5) / 128

        question = questions_val[index]
        answer = answers_val[index]

        questions.append(question)
        targets.append(answer)

    data = pad_collate(batch)
    imgs, questions, targets = data
    max_target_len = targets.size()[1]
    outputs = model.forward(imgs, questions, max_target_len)
    preds = F.softmax(outputs, dim=-1)
    _, pred_ids = torch.max(preds, dim=1)
    _pred_ids += list(pred_ids.cpu().numpy())

    for i in range(10):
        question = questions[i]
        question = ''.join([IVOCAB[id] for id in question]).replace('<EOS>', '')
        target = targets[i]
        target = ''.join([IVOCAB[id] for id in target]).replace('<EOS>', '')

        pred = _pred_ids[i]
        pred = ''.join([IVOCAB[id] for id in pred]).replace('<EOS>', '')

        print('提问：' + question)
        print('标准答案：' + target)
        print('电脑抢答：' + pred)
        print()
