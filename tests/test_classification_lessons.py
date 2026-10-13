import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manage_lessons',ROOT/'scripts/manage.py');manage=importlib.util.module_from_spec(spec);spec.loader.exec_module(manage)
class ClassificationLessonTests(unittest.TestCase):
 def test_every_guide_has_anatomy_and_stage_specific_illustrated_lessons(self):
  cases,refs=manage.load_and_validate(ROOT);schemas,_,_=manage.load_visuals(ROOT,cases)
  for g in manage.load_classifications(ROOT,cases,refs,schemas):
   with self.subTest(guide=g['id']):
    v=g.get('visual');self.assertIsInstance(v,dict);self.assertEqual(v['viewBox'],'0 0 960 640');self.assertGreaterEqual(len(v['labels']),4);self.assertGreaterEqual(len(v['stages']),4)
    for s in v['stages']:
     self.assertTrue(s['id'] and s['code']);self.assertEqual(set(s['explanation']),{'de','en','es'});self.assertEqual(set(s['boundary']),{'de','en','es'});self.assertNotEqual(s['svg'],v['anatomy']);self.assertTrue(set(s['cases'])<=set(g['cases']))
 def test_drawing_parser_supports_only_existing_local_gradients_and_inert_text(self):
  svg='<defs><linearGradient id="tissue"><stop offset="0" stop-color="#eee"/><stop offset="1" stop-color="#bbb"/></linearGradient></defs><path d="M0 0L1 1" fill="url(#tissue)"/><text x="20" y="20" data-label="kidney">1</text>'
  manage.svg_tree(svg,'test')
  for bad in [svg.replace('url(#tissue)','url(https://example.com/a.svg)'),svg.replace('url(#tissue)','url(#missing)'),svg+'<image href="https://example.com/a.png"/>',svg+'<script/>',svg.replace('data-label="kidney"','onclick="alert(1)"')]:
   with self.subTest(bad=bad),self.assertRaises(manage.ValidationError):manage.svg_tree(bad,'test')
 def test_rcc_distinguishes_venous_height_wall_and_fat(self):
  g=next(g for g in json.loads((ROOT/'data/classifications.json').read_text())['guides'] if g['id']=='rcc');s={s['id']:s for s in g['visual']['stages']}
  for id in ('t3a-fat','t3a-vein','t3b','t3c-height','t3c-wall','t4'):self.assertIn(id,s)
  self.assertNotEqual(s['t3b']['svg'],s['t3c-height']['svg']);self.assertNotEqual(s['t3c-height']['svg'],s['t3c-wall']['svg'])
 def test_nodal_maps_follow_the_primary_site(self):
  guides={g['id']:g for g in json.loads((ROOT/'data/classifications.json').read_text())['guides']}
  for id,sites in [('utuc',('proximal','distal')),('urethral',('posterior','anterior'))]:
   stages={s['id']:s for s in guides[id]['visual']['stages']}
   for site in sites:self.assertIn('n1-'+site,stages)
   self.assertNotEqual(stages['n1-'+sites[0]]['svg'],stages['n1-'+sites[1]]['svg'])
  s=next(s for s in guides['urethral']['visual']['stages'] if s['id']=='n1-anterior');words=' '.join(l['text']['en'].lower() for l in s['labels']);self.assertIn('inguinal',words);self.assertIn('pelvic',words)
 def test_unknown_practice_cases_and_unsafe_drawings_are_rejected(self):
  cases,refs=manage.load_and_validate(ROOT);schemas,_,_=manage.load_visuals(ROOT,cases);data=json.loads((ROOT/'data/classifications.json').read_text())
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for field,value in [('cases',['unknown']),('svg','<script/>')]:
    bad=copy.deepcopy(data);bad['guides'][0]['visual']['stages'][0][field]=value;manage.write_json(root/'data/classifications.json',bad)
    with self.assertRaises(manage.ValidationError):manage.load_classifications(root,cases,refs,schemas)
