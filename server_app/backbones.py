#!/usr/bin/env python

import os
import pexpect
import traceback
import logging

class Julius(object):
    def __init__(
        self,
        julius_path='/usr/local/bin/julius',
        main_conf='/usr/local/dictation-kit/main.jconf',
        grammer_conf='/usr/local/dictation-kit/am-gmm.jconf'
    ):
        self.sh = pexpect.spawn(
            '%s -C %s -C %s -nostrip -input rawfile' % (
                julius_path, main_conf, grammer_conf
            )
        )
    
    def __del__(self):
        self.sh.close()

    def speech_to_text(self, wavefile_path):
        try:
            if not os.path.exists(wavefile_path):
                raise Exception('wave file not exists')
            logging.error('entering filename')
            self.sh.expect('enter filename->')
            self.sh.sendline(wavefile_path)
            logging.error('filename entered')
            self.sh.expect('pass1_best: ')
            self.sh.expect('pass1_best_wordseq: ')
            pass1_sentence = self.sh.before.decode(encoding='utf-8').strip()
            logging.error('get passphases')
            self.sh.expect('pass1_best_phonemeseq: ')
            pass1_wordseq = self.sh.before.decode(encoding='utf-8').strip().replace('<s>', '').replace('</s>', '')
            self.sh.expect('pass1_best_score: ')
            pass1_phonemeseq = self.sh.before.decode(encoding='utf-8').strip()
            self.sh.expect('###')
            pass1_score = float(self.sh.before)
            return {
                'sentence': pass1_sentence,
                'wordseq': pass1_wordseq,
                'phonemeseq': pass1_phonemeseq,
                'score': pass1_score
            }
        except:
            logging.error(traceback.format_exc())
            return {}
