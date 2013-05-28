#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

'''
@description Assignment 4 for Software Testing in Spring 2013.
@author Lhfcws (Wenjie Wu, 10389393)
@email lhfcws@gmail.com
@notes I've done some changes in BNF input file, but what I can guarantee is that it is still legal BNF. 
'''

import sys
import re
from random import random

# GLOBAL VARS
K = 0
TEAM_PLAYER_NUMBER = 0
# -----------------------------------
'''
@class BNFSentence
@description A sentence of BNF grammar
'''
class BNFSentence(object):
	def __init__(self, sentence_):
		'''
		type_: 
			'|': or
			' ': concat
		star: If there's a * at the end of the whole sentence.
		qmark: If the sentence is like 'a+' in RE. Example: word {' ' word}
		iterative: If key = sentence is like A ::= A B or A ::= B A , which is iterative.
		sentence: The whole sentence.
		# referred: If this sentence was referred. This attribution works iff self.atom == True
		atom: If this sentence is an atom sentence. (not a terminal)
		terminal: If thie sentence is a terminal sentence like '1'.
		'''
		self.type_ = ' '
		self.star = False
		self.qmark = False
		self.sentence = sentence_.strip()
		self.atom = False
		self.terminal = False
		self.children = []
		self.content = None

		# Define the value of attributes above
		self.firstCheck()

		__sentence = self.sentence
		if self.star or self.qmark:
			self.children.append(__sentence[1:-1])
		elif not self.terminal and not self.atom:
			self.children = self.split(__sentence)

	# BNF Sentence split.
	def split(self, sentence):
		stack = []
		# Use some special characters to replace type_char (' ', '|')
		trans_ = {'|':'\$or\$', ' ':'\$br\$'}
		trans = {'|':'$or$', ' ':'$br$'}
		__sentence = []
		__sentence[:] = sentence[:]

		for i,c in enumerate(__sentence):
			if c == '{' or c == '[':
				if len(stack) == 0:
					stack.append(i)
				continue
			if c == self.type_:
				if len(stack) != 0:
					__sentence[i] = trans[c]
				continue
			if c == '\'':
				if len(stack) == 0:
					stack.append(i)
					continue
				elif __sentence[stack[-1]] == '\'':
					stack.pop()
			if c == '}' and len(stack) > 0 and __sentence[stack[-1]] == '{':
				stack.pop()
			if c == ']' and len(stack) > 0 and __sentence[stack[-1]] == '[':
				stack.pop()

		result = ''.join(__sentence).split(self.type_)
		# Replace the normal type_char back.
		for i,val in enumerate(result):
			p = re.compile(trans_[self.type_])
			result[i] = p.sub(self.type_, val).strip()

		return result
		
	# First Check to define meta information.	
	def firstCheck(self):

		p = re.compile('([A-Z]|[a-z]|_)+')
		mtch = p.match(self.sentence)
		if mtch != None and mtch.group() == self.sentence:
			self.atom = True
			return

		ln = len(self.sentence)
		stack = []
		match = [0] * ln

		for i,c in enumerate(self.sentence):
			if c == '{' or c == '[':
				stack.append(i)
				continue
			if c == '|':
				if len(stack) == 0:
					self.type_ = '|'
				continue
			if c == '\'':
				if len(stack) > 0 and self.sentence[stack[-1]] == '\'':
					stack.pop()
				else:
					stack.append(i)

			if c == '}' and len(stack) > 0 and self.sentence[stack[-1]] == '{':
				match[i] = stack[-1]
				match[stack[-1]] = i
				stack.pop()
			if c == ']' and len(stack) > 0 and self.sentence[stack[-1]] == '[':
				match[i] = stack[-1]
				match[stack[-1]] = i
				stack.pop()

		if self.sentence[0] == '[' and self.sentence[-1] == ']' and match[0] == ln - 1:
			self.qmark = True
			return

		if self.sentence[0] == '{' and self.sentence[-1] == '}' and match[0] == ln - 1:
			self.star = True
			return
		
		if self.sentence[0] == self.sentence[-1] == '\'' and self.sentence[1:-1].find('\'') == -1:
			self.terminal = True
			self.content = self.sentence[1:-1]
			return
		# Final return
		return

	# Debug Output
	def debug(self):
		print 'Sentence: ', self.sentence

		ch = []
		for i in self.children:
			if type(i) == type(''):
				ch.append(i)
			else:
				ch.append(i.sentence)

		print 'Children: ', ch
		print 'Attributes: '
		print '  star: ', self.star
		print '  qmark: ', self.qmark
		print '  atom: ', self.atom
		print '  terminal: ', self.terminal
		print '  content: ', self.content
	
# ---------------------------------------
'''
@class BNFParser
@description Parser to parse bnf grammar.
'''
class BNFParser(object):
	def __init__(self, bnf_content):
		self.__bnf = bnf_content
		self.__refer = set()
		self.tree = {}
		self.root = None

	# Split a BNF line into left and right.
	def __split_line(self, line):
		l = line.split('::=')
		l = stripList(l)

		return l

	# Parse a line into BNFSentence
	def __parse_line(self, line):
		ls = self.__split_line(line)
		self.temp_key = ls[0]
		self.tree[self.temp_key] = BNFSentence(ls[1])

		# Process BNFSentence recursively.
		self.__recursive_parse(self.tree[self.temp_key])
		
	def __recursive_parse(self, bnfs):
		if bnfs.atom:
			self.__refer.add(bnfs.sentence)
			return
		if bnfs.terminal:
			return
		
		for i, children in enumerate(bnfs.children):
			bnfs.children[i] = BNFSentence(children)
			self.__recursive_parse(bnfs.children[i])

	# Parse whole text.
	def parse(self):
		for line in self.__bnf:
			self.__parse_line(line)

		self.getRoot()

	# Get the Final non-terminal
	def getRoot(self):
		for key, item in self.tree.iteritems():
			if not key in self.__refer:
				self.root = key
				break
		return self.root
# ---------------------------------------
'''
@class TestGenerator
@description Generate test cases by parse tree.
'''
class TestGenerator(object):
	def __init__(self, parser_, max_iter_level):
		self.parser = parser_
		self.max_level = max_iter_level

	# Just make output more readable.
	def output_format(self,result):
		# Strip number like 012 to 12
		while True:
			p = re.compile('(>|,|\()0\d*')
			_result = p.sub(lambda m: m.group(0)[0]+''.join(m.group(0).split(m.group(0)[0]+'0'))+'1', result)
			if result == _result:
				break

			result = _result

		# Add some indents into the result file.
		p = re.compile('<')
		result = p.sub("\n<", result)

		p = re.compile('<length>|<width>|<name>|<numberOfPlayers>|<strategy>')
		result = p.sub(lambda m: '\t'+m.group(0)+'\n\t\t', result)
		p = re.compile('<\\\\length>|<\\\\width>|<\\\\name>|<\\\\numberOfPlayers>|<\\\\strategy>')
		result = p.sub(lambda m: '\t'+m.group(0), result)
		p = re.compile('<region>')
		result = p.sub(lambda m: '\t\t'+m.group(0)+'\n\t\t\t', result)
		p = re.compile('<\\\\region>')
		result = p.sub(lambda m: '\t\t'+m.group(0), result)

		p = re.compile('<\\\\end pitch>|<\\\\end team>')
		result = p.sub(lambda m: m.group(0)+'\n', result)
		p = re.compile('<begin pitch>')
		result = p.sub(lambda m: '\n' + m.group(0), result)

		return result

	# Generate test cases after Parser finished.
	def generate(self, index=1):
		assert(self.parser.root != None)
		global K

		def iter_gen(sentence, dep, key):
			# If sentence is a terminal.
			if sentence.terminal:
				return sentence.content
			
			# If sentence is an atom sentence like TEAM_STRATEGY
			if sentence.atom:
				return iter_gen(self.parser.tree[sentence.sentence], dep, sentence.sentence)
			
			# Equals to /(\w)?
			if sentence.qmark:
				r = randomPick([True, False])
				if not r:
					return ''
				return iter_gen(sentence.children[0], dep, key)

			# Equals to /(\w)*
			if sentence.star:
				r = randomPick(xrange(K))
				if key == 'TEAM_REGIONS':
					global TEAM_PLAYER_NUMBER
					r = TEAM_PLAYER_NUMBER - 1
				_line = []
				for i in xrange(0,r+1):
					_line.append(iter_gen(sentence.children[0], dep, key))
				return ''.join(_line)

			# Separate by type_char
			if sentence.type_ == '|':
				r = randomPick(sentence.children)
				while contains(r.sentence, key) and dep > K:
					r = randomPick(sentence.children)
				if contains(r.sentence, key):
					return iter_gen(r, dep+1, key)
				else:
					temp = iter_gen(r, dep, key)
					if key == 'TEAM_NUMBER_OF_PLAYERS':
						global TEAM_PLAYER_NUMBER
						TEAM_PLAYER_NUMBER = int(temp)
					return temp
			elif sentence.type_ == ' ':
				_line = []
				for i in sentence.children:
					_line.append(iter_gen(i, dep, key))
			
				return ''.join(_line)


		result = iter_gen(self.parser.tree[self.parser.root], 0, self.parser.root)
		result = self.output_format(result)
		return result

###################################################
### Common Functions
# If A contains B.
def contains(s1, s2):
	return s1.find(s2) != -1

# Pick up an element from list randomly.
def randomPick(ls):
	r = int(random() * 100000) % len(ls)
	return ls[r]	

# Strip a list.
def stripList(ls):
	for i, l in enumerate(ls):
		if type(l) == type(''):
			ls[i] = l.strip()

	return ls

# Get BNF file content.
def getBNFFile():
	filename = 'sts.bnf'
	fs = open(filename, 'r')
	bnf_lines = fs.readlines()
	fs.close()

	return bnf_lines


def main():
	# Interact
	print 'Loading `sts.bnf`...'
	content = getBNFFile()
	global K
	K = int(raw_input('Please input the max iterative level K (integer):'))
	K = K > 0 and K or 0

	# Process
	parser = BNFParser(content)
	parser.parse()
	runner = TestGenerator(parser, K)
	
	result = []
	for index in xrange(1,6):
		result.append(runner.generate(index))
	
	# Output
	fp = open('result.txt', 'w')
	for i, res in enumerate(result):
		fp.write('\n')
		fp.write('======== TEST CASE '+str(i)+' ===========\n')
		fp.write(res)
		fp.write('\n')
		fp.write('==================================\n')
	fp.close()
	pass

#####################################################

if __name__ == '__main__':
	main()

