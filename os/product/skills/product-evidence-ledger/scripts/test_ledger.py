import csv, importlib.util, json, sqlite3, tempfile, unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ledger import sync, review_queue

class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name);self.db=self.root/'test.sqlite'
    def tearDown(self):self.tmp.cleanup()
    def file(self,name='facts',rows=None):
        p=self.root/(name+'.csv')
        with p.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerows(rows or [['id','text'],['P1','中文,换行\n内容']])
        return p
    def count(self):
        with sqlite3.connect(self.db) as c:return c.execute('select count(*) from history').fetchone()[0]
    def test_idempotence_and_revision(self):
        p=self.file();self.assertEqual(sync(self.db,[p]),1);self.assertEqual(sync(self.db,[p]),0)
        self.file(rows=[['id','text'],['P1','修订']]);self.assertEqual(sync(self.db,[p]),1);self.assertEqual(self.count(),2)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(json.loads(c.execute('select payload from current').fetchone()[0])['text'],'修订')
    def test_atomic_batch(self):
        p=self.file();sync(self.db,[p]);self.file(rows=[['id','text'],['P1','changed']])
        bad=self.file('broken',[['id','text'],['X','a'],['X','b']])
        with self.assertRaises(ValueError):sync(self.db,[p,bad])
        self.assertEqual(self.count(),1)
    def test_missing_is_not_deleted(self):
        p=self.file();sync(self.db,[p]);self.file(rows=[['id','text']]);self.assertEqual(sync(self.db,[p]),0);self.assertEqual(self.count(),1)
    def test_invalid_input(self):
        for rows in ([['text'],['a']],[['id','id'],['x','y']],[['id','text'],['','x']],[['id','text'],[' X','x']],[['id','text'],['X']],[['id','text'],['X','a','extra']]):
            with self.assertRaises(ValueError):sync(self.db,[self.file(rows=rows)])
    def test_concurrent_same_record(self):
        p=self.file()
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(lambda _:sync(self.db,[p]),range(2)))
        self.assertEqual(sum(result),1);self.assertEqual(self.count(),1)
    def test_text_is_data_and_unicode_roundtrip(self):
        value="'); DROP TABLE history; -- 中文\n第二行"
        sync(self.db,[self.file(rows=[['id','text'],['P1',value]])])
        with sqlite3.connect(self.db) as c:self.assertEqual(json.loads(c.execute('select payload from current').fetchone()[0])['text'],value)
    def test_queue(self):
        p=self.file('market',[['id','复核结论'],['M1','核心陈述获一手支持'],['M2','部分支持']]);sync(self.db,[p]);before=self.count()
        self.assertEqual(list(review_queue(self.db))[0][0],'M2');self.assertEqual(self.count(),before)
    def test_invalid_dataset(self):
        with self.assertRaises(ValueError):sync(self.db,[self.file('bad-name')])

if __name__=='__main__':unittest.main(verbosity=2)
