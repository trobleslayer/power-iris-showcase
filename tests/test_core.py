import unittest
from power_iris.core import retrieve, Node
class CoreTest(unittest.TestCase):
    def test_retrieval(self):
        rows=[{'text':'voltage stability power flow'},{'text':'weather wind'}]
        self.assertEqual(retrieve(rows,['voltage stability'],1),rows[:1])
    def test_backprop(self):
        r=Node(0,'root',{}, {},0,[]); n=Node(1,'x',{}, {},.5,[],r); n.update(.5); self.assertEqual((r.visits,r.total),(1,.5))
if __name__=='__main__': unittest.main()
