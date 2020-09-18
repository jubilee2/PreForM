import unittest
import tempfile
import os

from PreForM.PreForM import PFMdirective, Macros, State, ParsedLine, preprocess_file, main

class TestPreprocessFile(unittest.TestCase):
  def setUp(self):
    self.pline = ParsedLine()
    self.macros_ = Macros()
    self.state_ = State()
    self.pfmdir_ = PFMdirective()


  def test_preprocess_file_1(self):
    tmpPath = tempfile.gettempdir()
    foo_path = os.path.join(tmpPath, "foo.f90")
    foo_out_path = os.path.join(tmpPath, "foo_out.f90")
    foo = """#define FIRST
#ifdef FIRST
print*,'Ok, "define" and "ifdef-else" work!'
#else
print*,'No, something is wrong with "define" and "ifdef-else"!'
#endif
#undef FIRST
#ifdef FIRST
print*,'No, something is wrong with "undef" and "ifdef-else"!'
#else
print*,'Ok, "undef" and "ifdef-else" work!'
#endif
 """
    foo_out = """print*,'Ok, "define" and "ifdef-else" work!'
print*,'Ok, "undef" and "ifdef-else" work!'
 """
    foo_out = foo_out.split('\n')
    foo_out = [ s + '\n' for s in foo_out]
    foo_out[-1] = foo_out[-1].rstrip('\n')

    with open(foo_path, "w") as f:
      f.writelines(foo)

    parsed_file_ = open(foo_out_path, 'w')
    preprocess_file(foo_path, parsed_file_, self.macros_ , self.state_, self.pfmdir_)

    parsed_file_.close()
    with open(foo_out_path, 'r') as f:
      out = f.readlines()

    self.assertEqual(out, foo_out)

    if os.path.exists(foo_path):
      os.remove(foo_path)
    if os.path.exists(foo_out_path):
      os.remove(foo_out_path)

  def test_preprocess_file_2(self):
    tmpPath = tempfile.gettempdir()
    foo_path = os.path.join(tmpPath, "foo.f90")
    foo_out_path = os.path.join(tmpPath, "foo_out.f90")
    foo = """#define FIRST
#ifdef THIRD
print*, 'No, something is wrong with "ifdef"!'
#elif defined FIRST
print*,'Ok, "elif" works!'
#endif
 """
    foo_out = """print*,'Ok, "elif" works!'
 """
    foo_out = foo_out.split('\n')
    foo_out = [ s + '\n' for s in foo_out]
    foo_out[-1] = foo_out[-1].rstrip('\n')

    with open(foo_path, "w") as f:
      f.writelines(foo)

    parsed_file_ = open(foo_out_path, 'w')
    preprocess_file(foo_path, parsed_file_, self.macros_ , self.state_, self.pfmdir_)

    parsed_file_.close()
    with open(foo_out_path, 'r') as f:
      out = f.readlines()

    self.assertEqual(out, foo_out)

    if os.path.exists(foo_path):
      os.remove(foo_path)
    if os.path.exists(foo_out_path):
      os.remove(foo_out_path)

if __name__ == '__main__':
    unittest.main()