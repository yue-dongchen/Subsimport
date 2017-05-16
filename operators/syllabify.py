import bpy
from bpy_extras.io_utils import ExportHelper

import os

from .hyphenator.hyphenator import Hyphenator
from .hyphenator.get_dictionary import get_dictionary

from .tools.get_text_strips import get_text_strips
from .tools.remove_punctuation import remove_punctuation

def collect_words(scene):
    """Collect, clean, and alphabetize the words in the subtitles"""
    
    words = []
        
    text_strips = get_text_strips(scene)
    for strip in text_strips:
        strip_words = strip.text.lower().replace('\n', ' ').split(' ')
        words.extend(strip_words)
    
    i = 0
    while i < len(words):
        if words[i].rstrip() == '':
            words.pop(i)
        else:
            i += 1
            
    words = set(words)
    words = list(sorted(words))
    
    for i in range(len(words)):
        words[i] = remove_punctuation(words[i])
    
    return words

def get_patterns(lang):
    """Get language patterns for the given language"""
    module_path = os.path.dirname(__file__)
    pat_path = os.path.join(
        module_path, 'hyphenator', 'patterns', lang + '.txt')
    f = open(pat_path, 'r', encoding='utf-8')
    patterns = f.read()
    f.close()
    
    return patterns
        

class Syllabify(bpy.types.Operator, ExportHelper):
    bl_label = 'Syllabify'
    bl_idname = 'sequencerextra.syllabify'
    bl_description = "Create a list of words, separated by syllables.\nNeeded for splitting words with accurate syllable differentiation"
    
    filename_ext = ".txt"
    
    @classmethod
    def poll(self, context):
        scene = context.scene
        try:
            text_strips = get_text_strips(scene)
            
            if len(text_strips) > 0:
                return True
            else:
                return False
        except AttributeError:
            return False
    
    def execute(self, context):
        scene = context.scene
        
        words = collect_words(scene)
        
        found_words = []
        if scene.use_dictionary_syllabification:
            dictionary = get_dictionary(
                lang=scene.syllabification_language)
            for i in range(len(words)):
                try:
                    words[i] = dictionary[words[i]]
                    found_words.append(words[i])
                except KeyError:
                    pass
                    
        if scene.use_algorithmic_syllabification:
            hyphenator = Hyphenator()
            patterns = get_patterns(scene.syllabification_language)
            hyphenator.patterns = patterns
            hyphenator.setup_patterns()
            for i in range(len(words)):
                if not words[i] in found_words:
                    words[i] = hyphenator.hyphenate_word(words[i])
                    words[i] = ' '.join(words[i])
        
        f = open(self.filepath, 'w')
        f.write('\n'.join(words))
        f.close()
        
        scene.syllable_dictionary_path = self.filepath
        
        return {"FINISHED"}