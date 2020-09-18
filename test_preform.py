import unittest

from PreForM.PreForM import PFMdirective, Macros, State, ParsedLine, preprocess_file, main

class TestPFMdirective(unittest.TestCase):
  def setUp(self):
    self.pfmdir = PFMdirective()

  def test_add_to_block(self):
    self.pfmdir.add_to_block('Foo')
    self.assertEqual(self.pfmdir.block_contents[0], 'Foo')

  def test_execute(self):
    self.pfmdir.for_block = True
    self.pfmdir.for_expression = 'for i in [1,2,3]:'
    self.pfmdir.add_to_block('module procedure foo$i')
    result = self.pfmdir.execute()
    self.assertEqual(result, 'module procedure foo1\nmodule procedure foo2\nmodule procedure foo3\n')

class TestMacros(unittest.TestCase):
  def setUp(self):
    self.macros = Macros()

  def test_init(self):
    macros = Macros({'foo': 'bar'})
    self.assertIsInstance(self.macros.dic, dict)
    self.assertEqual(macros.dic, {'foo': 'bar'})

  def test_set(self):
    self.macros.set('foo2', 'bar2')
    self.assertEqual(self.macros.dic['foo2'], 'bar2')

  def test_is_def(self):
    self.assertTrue(self.macros.is_def('__FILE__'))
    self.assertFalse(self.macros.is_def('bar'))

  def test_is_undef(self):
    self.assertFalse(self.macros.is_undef('__FILE__'))
    self.assertTrue(self.macros.is_undef('bar'))

  def test_expand(self):
    self.macros.set('foo2', 'bar2')
    self.assertEqual(self.macros.expand('hello foo2'),'hello bar2')

    self.macros.set('MYPRINT(x)', "print*,'Ok ',x,' works!'")
    i_str = "MYPRINT('simple function-like macros')"
    o_str = "print*,'Ok ','simple function-like macros',' works!'"
    self.assertEqual(self.macros.expand(i_str),o_str)

    self.macros.set('MYWARN(COND)', "if (COND) print*,'Ok, stringification of '//#COND//' works!'")
    i_str = "MYWARN(x<2.0)"
    o_str = "if (x<2.0) print*,'Ok, stringification of '//\"x<2.0\"//' works!'"
    self.assertEqual(self.macros.expand(i_str),o_str)

    self.macros.set('MYCONCAT(x)', "print*,'Ok, x ## -operator works!'")
    i_str = "MYCONCAT(concatenation)"
    o_str = "print*,'Ok, concatenation-operator works!'"
    self.assertEqual(self.macros.expand(i_str),o_str)

    self.macros.set('VARIADIC_MACRO(...)', "print*,'Ok,',#__VA_ARGS__,' works also within stringification operator!'")
    i_str = "VARIADIC_MACRO(foo,bar)"
    o_str = "print*,'Ok,',\"foo\",\"bar\",' works also within stringification operator!'"
    self.assertEqual(self.macros.expand(i_str),o_str)

  def test_evaluate(self):
    self.macros.set('FIRST', '')
    self.macros.set('SECOND', '')
    self.assertTrue(self.macros.evaluate('defined FIRST'))
    self.assertTrue(self.macros.evaluate('defined FIRST && defined SECOND'))
    self.assertFalse(self.macros.evaluate('defined FIRST && defined FOO'))
    self.assertTrue(self.macros.evaluate('2 > 1'))

  def test_list(self):
    self.macros.set('undefinedFoo', None)
    self.macros.list()

  def test_get_from_cli(self):
    self.macros.get_from_cli(["foo=bar"])
    self.assertEqual(self.macros.dic['foo'],'bar')

    self.macros.get_from_cli(["foo1=bar1","foo2=bar2"])
    self.assertEqual(self.macros.dic['foo1'],'bar1')
    self.assertEqual(self.macros.dic['foo2'],'bar2')

  def test_undef(self):
    self.macros.dic['foo1'] = 'bar'
    self.macros.undef('foo1')
    self.assertIsNone(self.macros.dic['foo1'])

class TestState(unittest.TestCase):
  def test_init(self):
    state = State()
    self.assertEqual(state.action, 'print')
    self.assertEqual(state.scope, 'normal')
    self.assertEqual(state.include, '')

    state = State('foo', 'bar', 'foobar')
    self.assertEqual(state.action, 'foo')
    self.assertEqual(state.scope, 'bar')
    self.assertEqual(state.include, 'foobar')

class TestParsedLine(unittest.TestCase):
  def setUp(self):
    self.pline = ParsedLine()
    self.macros_ = Macros()
    self.state_ = State()
    self.pfmdir_ = PFMdirective()

  def test_init(self):
    pline = ParsedLine()
    self.assertEqual(pline.line, '')

    pline1 = ParsedLine('foo')
    self.assertEqual(pline1.line, 'foo')

  def test_preproc_check(self):
    # cpp directives
    self.assertFalse(self.macros_.is_def('Foo'))
    self.pline.line = '#define Foo'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertTrue(self.macros_.is_def('Foo'))

    self.pline.line = '#define Foo abcd'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertTrue(self.macros_.is_def('Foo'))
    self.assertEqual(self.macros_.dic['Foo'], 'abcd')

    self.assertTrue(self.macros_.is_def('Foo'))
    self.pline.line = '#undef Foo'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertTrue(self.macros_.is_undef('Foo'))

    self.pline.line = '#include "abc.inc"'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'include')
    self.assertEqual(self.state_.include, 'abc.inc')

    # cpp conditional directives
    self.macros_.dic['Foo'] = ''
    self.pline.line = '#ifdef Foo'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'print')

    self.pline.line = '#ifdef Foo1'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'omit')

    self.pline.line = '#elif defined Foo'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'print')

    self.pline.line = '#elif defined Foo1'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'omit')

    self.pline.line = '#ifndef Foo1'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'print')

    self.pline.line = '#ifndef Foo'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'omit')

    self.state_.scope = 'omit'
    self.pline.line = '#else'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'print')

    self.state_.scope = 'print'
    self.pline.line = '#else'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'omit')

    self.pline.line = '#endif'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'normal')


    self.setUp()
    self.pline.line = '#PFM for i in range(1,4):'
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'omit')
    self.assertEqual(self.state_.scope, 'for_block')
    self.assertTrue(self.pfmdir_.for_block)
    self.assertEqual(self.pfmdir_.for_expression, ' for i in range(1,4):')

    self.pline.line = "  module procedure less_than_type_$i"
    self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_)

    self.pline.line = '#PFM endfor '
    self.assertIsNone(self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.assertEqual(self.state_.action, 'print')
    self.assertEqual(self.state_.scope, 'print')
    self.assertFalse(self.pfmdir_.for_block)
    self.assertEqual(self.pfmdir_.for_expression, '')
    self.assertEqual(self.pfmdir_.block_contents, [])

    result = [
      "  module procedure less_than_type_1\n",
      "  module procedure less_than_type_2\n",
      "  module procedure less_than_type_3\n"
    ]
    lines = "".join(result)
    self.assertEqual(self.pline.line, lines)

    self.pline.line = "print hello"
    self.state_.scope = 'print'
    self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_)
    self.state_.action, 'print'

    self.state_.scope = 'omit'
    self.pline.preproc_check(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_)
    self.state_.action, 'omit'

  def test_parse(self):
    self.pline.line = 'today: __DATE__:'
    self.assertTrue('today:' in self.pline.parse(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))

    self.pline.line = 'hello bar'
    self.assertEqual(self.pline.parse(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_), 'hello bar')

    self.pline.line = '#include "abc.inc"'
    self.assertIsNone(self.pline.parse(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))
    self.pline.line = '#else'
    self.assertIsNone(self.pline.parse(macros=self.macros_, state=self.state_, pfmdir=self.pfmdir_))

