# -*- coding: utf-8 -*
import os
import tqdm
from dataclasses import dataclass
from deeppavlov import configs, build_model
from more_itertools import split_before
from utils import read_file, prep_text

DATA_DIR = 'data'

claimant_prev = ['по иску', 'истец', 'по заявлению', 'заявление', ' гр ', 'гражданина', 'гражданки',
                 'гражданином', 'гражданкой',  'гражданину', 'гражданке', 'заявитель', 'заявителем',
                 'до сведения', 'информации о', 'обращение', 'обращению', 'обращения', 'претензия',
                 'претензию', 'ходатайство', 'обратился', 'обратилась', 'обратилось', 'согласие',
                 'гр - ке', 'гр ну', 'гр ки', 'гр на']
claimant_post = ['обратился', 'обратилась', 'обратилось', 'удовлетворить', 'на получение смс', 'далее заявитель']
defendant_prev = ['иском к', 'взыскать с', 'в отношении', 'вина', 'виновным', 'привлечь',
                  'о нарушении', 'в действиях', 'привлечении', 'виновности', 'назначении наказания',
                  'назначить', 'ответчик', 'признать', 'в адрес', 'вину', 'вины',
                  'ответственности', 'к административной ответственности', 'вмененного',
                  'привлекаемого', 'виновность', 'привлечение', 'совершенного', 'привлечения']
defendant_post = ['в совершении', 'виновным', 'совершило', 'совершил', 'было совершено', 'привлечено',
                  'наказание', 'признает', 'вину', 'признать виновным', 'составлен',
                  'выполнило требования', 'установлена', 'подтверждается', 'протокол', 'нарушение', 'совершила',
                  'в совершении', 'к ответственности', 'к административной', 'вменяется']


@dataclass
class Entity:
    """
    entity: entity
    categ: entity category (PER - person or ORG - organisation)
    prev_context: previous context
    post_context: post context
    """
    entity: str
    categ: str
    prev_context: str
    post_context: str


class Extractor:
    def __init__(self):
        self.model = build_model(configs.ner.ner_rus_bert)
        self.output = {}

    def _find_entities(self, text):
        for par in prep_text(text):
            try:
                pred = self.model([par])
                tokens = ['<EMPTY>'] * 5 + pred[0][0] + ['<EMPTY>'] * 5
                tags = ['O'] * 5 + pred[1][0] + ['O'] * 5
                target_tags = [(idx, tag) for idx, tag in enumerate(tags) if tag.endswith('ORG') or tag.endswith('PER')]
                if target_tags:
                    positions = split_before(target_tags, lambda x: x[1].startswith('B'))
                    for item in positions:
                        start, end = item[0][0], item[-1][0] + 1
                        yield Entity(entity=' '.join(tokens[start:end]),
                                     categ=item[0][1].split('-')[-1],
                                     prev_context=' '.join(t for t in tokens[start - 5:start] if t.isalpha()).lower(),
                                     post_context=' '.join(t for t in tokens[end:end + 5] if t.isalpha()).lower())
            except IndexError:
                pass

    @staticmethod
    def _is_court(entity):
        return int(entity.categ == 'ORG' and 'суд' in entity.entity.lower().split())

    @staticmethod
    def _is_claimant(entity):
        prev_points = sum(1 for word in claimant_prev if word in entity.prev_context)
        post_points = sum(1 for word in claimant_post if word in entity.post_context)
        return prev_points + post_points

    @staticmethod
    def _is_defendant(entity):
        prev_points = sum(1 for word in defendant_prev if word in entity.prev_context)
        post_points = sum(1 for word in defendant_post if word in entity.post_context)
        return prev_points + post_points

    def process_docs(self, folder):
        for fname in tqdm.tqdm(os.listdir(os.path.join(DATA_DIR, folder)), desc=folder):
            result = {
                'court_name': None,
                'claimant_name': [],
                'defendant_name': []
            }
            for ent in self._find_entities(read_file(folder, fname)):
                if self._is_court(ent):
                    result['court_name'] = ent.entity
                claim_points = self._is_claimant(ent)
                defend_points = self._is_defendant(ent)
                if claim_points == defend_points == 0:
                    pass
                elif claim_points > defend_points:
                    result['claimant_name'].append((ent.entity, claim_points))
                elif claim_points < defend_points:
                    result['defendant_name'].append((ent.entity, defend_points))
                else:
                    pass
            if result['claimant_name']:
                result['claimant_name'] = max(result['claimant_name'], key=lambda x: x[1])[0]
            if result['defendant_name']:
                result['defendant_name'] = max(result['defendant_name'], key=lambda x: x[1])[0]

            self.output[fname] = result
