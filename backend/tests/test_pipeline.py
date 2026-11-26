import os, unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.generation import generate_project, validate_with_correction, _local_spec_v2, _lint_v2, plan_prompt
from backend.app.models import GenerateRequest, ProjectSpec
from backend.app.styles import STYLE_IDS, ALLOWED_PRESETS

EXAMPLE = "examples/reel-example.json"

class GenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_plan_is_valid_v2_and_tracks_requested_duration(self):
        os.environ.pop('LLM_API_KEY', None)
        spec, provider = await generate_project(GenerateRequest(prompt='Create a kinetic promo', duration=20, aspect_ratio='9:16'))
        self.assertEqual(provider, 'local')
        self.assertEqual(spec.version, 2)
        self.assertGreaterEqual(len(spec.scenes), 3)
        self.assertAlmostEqual(spec.duration, 20, places=1)
        self.assertTrue(all(s.layers for s in spec.scenes))
        self.assertTrue(all(s.camera.move != 'static' or s.duration < 3 for s in spec.scenes))
        self.assertEqual(spec.meta.width, 1080)

    async def test_every_layer_has_an_entrance_and_all_presets_allowed(self):
        os.environ.pop('LLM_API_KEY', None)
        spec, _ = await generate_project(GenerateRequest(prompt='A loud launch', duration=12, aspect_ratio='16:9'))
        for scene in spec.scenes:
            for layer in scene.layers:
                self.assertIsNotNone(layer.animation.in_, f"layer {layer.id} lacks an entrance animation")
                self.assertIn(layer.animation.in_.preset, ALLOWED_PRESETS)

    async def test_example_composition_validates(self):
        import json
        raw = json.load(open(EXAMPLE))
        spec, problems = validate_with_correction(raw, max_retries=0)
        self.assertEqual(len(spec.scenes), 3)
        self.assertEqual(spec.meta.style, 'bold-kinetic')
        self.assertTrue(all(s.layers for s in spec.scenes))

    async def test_lint_rejects_static_scene_and_unsafe_zones(self):
        raw = _local_spec_v2(GenerateRequest(prompt='a kinetic launch story', duration=8))
        spec = ProjectSpec.model_validate(raw)
        problems = _lint_v2(spec)
        self.assertEqual(problems, [])

    async def test_styles_and_presets_are_exposed(self):
        self.assertIn('bold-kinetic', STYLE_IDS)
        self.assertIn('pop-bounce', ALLOWED_PRESETS)
        self.assertIn('underline-draw', ALLOWED_PRESETS)

    async def test_llm_plan_schema_fields_and_preset_vocabulary_validate(self):
        # Mirrors the plan schema rather than relying on the local generator's
        # already-complete ProjectSpec payload.
        raw = {
            'meta': {'fps': 30, 'width': 1080, 'height': 1920, 'duration': 4, 'style': 'bold-kinetic'},
            'audio': {},
            'scenes': [{
                'id': 'scene-1', 'duration': 4,
                'background': {'type': 'animated-gradient', 'colors': ['#0B1020']},
                'camera': {'move': 'push-in', 'intensity': 0.5},
                'layers': [{
                    'id': 'layer-1', 'type': 'text', 'content': 'Hello world',
                    'start': 0, 'end': 4, 'position': {'x': 0.5, 'y': 0.5},
                    'animation': {'in': 'whip-in', 'loop': {'preset': 'leaf-drift'},
                                  'out': {'preset': 'circle-draw-on'}},
                }],
            }],
        }
        spec, _ = validate_with_correction(raw, max_retries=0, prompt_fallback='Create a kinetic promo',
                                           aspect_ratio='9:16')
        self.assertEqual(spec.title, 'Motion story')
        self.assertEqual(spec.prompt, 'Create a kinetic promo')
        self.assertEqual((spec.meta.width, spec.meta.height), (1080, 1920))
        layer = spec.scenes[0].layers[0]
        self.assertEqual(layer.animation.in_.preset, 'whip-in')
        self.assertEqual(layer.animation.loop.preset, 'leaf-drift')
        self.assertEqual(layer.animation.out.preset, 'circle-draw-on')
        self.assertIn('"title"', plan_prompt())
        self.assertIn('"prompt"', plan_prompt())

    async def test_llm_provider_failure_falls_back_to_local(self):
        os.environ['LLM_API_KEY'] = 'test-key'
        with patch('backend.app.generation._llm_spec_v2', new=AsyncMock(side_effect=RuntimeError('provider unavailable'))):
            spec, provider = await generate_project(GenerateRequest(prompt='Create a kinetic promo', duration=12))
        self.assertEqual(provider, 'local')
        self.assertEqual(spec.version, 2)

class ApiTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop('LLM_API_KEY', None)
        self.client=TestClient(app)

    def test_generate_to_saved_project_roundtrip(self):
        generated=self.client.post('/api/generate',json={'prompt':'Create a kinetic launch promo','duration':20,'aspect_ratio':'16:9'})
        self.assertEqual(generated.status_code,200,generated.text)
        result=generated.json()
        pid=result['id']
        self.assertEqual(result['provider'],'local')
        self.assertEqual(result['spec']['version'],2)
        saved=self.client.post('/api/projects',json={'id':pid,'spec':result['spec']})
        self.assertEqual(saved.status_code,200,saved.text)
        self.assertEqual(self.client.get(f'/api/projects/{pid}').status_code,200)
        self.client.delete(f'/api/projects/{pid}')

    def test_bad_prompt_and_bad_export_format_are_clear(self):
        self.assertEqual(self.client.post('/api/generate',json={'prompt':'short'}).status_code,422)
        self.assertEqual(self.client.post('/api/projects/no-such-project/export?format=avi').status_code,422)

if __name__=='__main__': unittest.main()
