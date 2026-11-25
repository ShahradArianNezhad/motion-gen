import os, unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.generation import generate_project, _compose_storyboard, _local_spec, validate_with_correction
from backend.app.models import GenerateRequest, ProjectSpec

class GenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_storyboard_is_valid_and_tracks_requested_duration(self):
        os.environ.pop('LLM_API_KEY', None)
        spec, provider = await generate_project(GenerateRequest(prompt='Create a Persian inventory management promo', duration=20, aspect_ratio='9:16'))
        self.assertEqual(provider, 'local')
        self.assertEqual(spec.language, 'fa')
        self.assertEqual(spec.aspect_ratio, '9:16')
        self.assertEqual((spec.width, spec.height), (1080, 1920))
        self.assertEqual(len(spec.scenes), 4)
        self.assertAlmostEqual(spec.duration, 20, places=1)
        self.assertTrue(all(scene.elements for scene in spec.scenes))

    async def test_bounded_preflight_repair_fixes_clipping_and_unsupported_motion(self):
        raw=_local_spec(GenerateRequest(prompt='inventory management',duration=20,aspect_ratio='16:9'))
        element=raw['scenes'][0]['elements'][1]
        element.update(x=100,width=90,color='not-a-color',animation='bounce',delay=99)
        spec,corrections=validate_with_correction(raw,max_retries=1)
        self.assertEqual(len(corrections),1)
        self.assertLessEqual(spec.scenes[0].elements[1].x+spec.scenes[0].elements[1].width/2,100)
        self.assertEqual(spec.scenes[0].elements[1].animation,'reveal')
        self.assertTrue(spec.scenes[0].elements[1].color.startswith('#'))

    async def test_storyboard_stage_composes_safe_persian_animation_components(self):
        req=GenerateRequest(prompt='ویدیوی معرفی محصول',duration=10,aspect_ratio='9:16')
        brief={'working_title':'معرفی محصول','language':'fa','palette':['#071A2D','#168AAD','#41EAD4']}
        story={'scenes':[
            {'title':'آغاز','duration':3,'visual_purpose':'ایجاد کنجکاوی','transition':'fade','narration':'با نگاهی تازه','on_screen_text':{'eyebrow':'آغاز','headline':'ایده‌ای تازه','supporting_copy':'برای کارهای مهم'}},
            {'title':'ارزش','duration':3,'visual_purpose':'نمایش مزیت','transition':'wipe','narration':'ساده‌تر پیش بروید','on_screen_text':{'eyebrow':'مزیت','headline':'همه‌چیز روشن','supporting_copy':'یک نمای دقیق و زنده'}},
            {'title':'پایان','duration':4,'visual_purpose':'دعوت به اقدام','transition':'zoom','narration':'از امروز شروع کنید','on_screen_text':{'eyebrow':'شروع','headline':'قدم بعدی شما','supporting_copy':'از همین امروز'}}]}
        spec=ProjectSpec.model_validate(_compose_storyboard(req,brief,story))
        self.assertEqual(spec.language,'fa')
        self.assertEqual(spec.aspect_ratio,'9:16')
        self.assertAlmostEqual(spec.duration,10,places=1)
        self.assertIn('headline',[el.kind for el in spec.scenes[0].elements])

    async def test_rejects_invalid_color_and_unbounded_coordinates(self):
        with self.assertRaises(Exception):
            ProjectSpec.model_validate({'title':'bad','prompt':'bad','scenes':[{'id':'a','title':'a','duration':2,'description':'x','background':'not-a-color','elements':[{'id':'e','x':120} ]},{'id':'b','title':'b','duration':2,'description':'x','elements':[{'id':'f'}]}]})

class ApiTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop('LLM_API_KEY', None)
        self.client=TestClient(app)

    def test_prompt_to_saved_project_to_safe_ai_edit(self):
        generated=self.client.post('/api/generate',json={'prompt':'Create an inventory management promo','duration':20,'aspect_ratio':'16:9'})
        self.assertEqual(generated.status_code,200,generated.text)
        result=generated.json()
        pid=result['id']
        self.assertEqual(result['provider'],'local')
        saved=self.client.post('/api/projects',json={'id':pid,'spec':result['spec']})
        self.assertEqual(saved.status_code,200,saved.text)
        edit=self.client.post('/api/edit',json={'project_id':pid,'command':'make the background darker'})
        self.assertEqual(edit.status_code,200,edit.text)
        self.assertTrue(all(s['background']=='#070B16' for s in edit.json()['project']['spec']['scenes']))
        self.assertEqual(self.client.get(f'/api/projects/{pid}').status_code,200)
        self.client.delete(f'/api/projects/{pid}')

    def test_bad_prompt_and_bad_export_format_are_clear(self):
        self.assertEqual(self.client.post('/api/generate',json={'prompt':'short'}).status_code,422)
        self.assertEqual(self.client.post('/api/projects/no-such-project/export?format=avi').status_code,422)

if __name__=='__main__': unittest.main()
