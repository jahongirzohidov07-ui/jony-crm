import ast, os, unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from teacher_response import response_text, generation_config

class TeacherResponseTests(unittest.TestCase):
    def test_parts_and_thoughts(self):
        self.assertEqual(response_text({"candidates":[{"content":{"parts":[{"thought":True,"text":"private reasoning"},{"text":"Hello! "},{"text":"How are you?"}]}}]}),"Hello! How are you?")
    def test_empty_and_blocked(self):
        for data in [{},{"candidates":[{"finishReason":"MAX_TOKENS"}]},{"promptFeedback":{"blockReason":"SAFETY"}}]:
            with self.assertRaises(ValueError): response_text(data)
    def test_generation_budget(self):
        self.assertEqual(generation_config("gemini-2.5-flash",160)["thinkingConfig"],{"thinkingBudget":0})
        self.assertEqual(generation_config("gemini-3-flash",160)["thinkingConfig"],{"thinkingLevel":"low"})
        self.assertEqual(generation_config("gemini-other",4096)["maxOutputTokens"],4096)
    def test_real_adapter_handles_multi_part_reply_and_filters_audio_models(self):
        tree=ast.parse(Path(__file__).with_name("student_app.py").read_text(encoding="utf-8"))
        fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_ai_reply")
        ns={"os":os}; exec(compile(ast.Module(body=[fun],type_ignores=[]),"adapter","exec"),ns)
        def response(data,status=200): return httpx.Response(status,json=data,request=httpx.Request("POST","https://example.test"))
        listing=response({"models":[{"name":"models/gemini-2.5-flash-tts","supportedGenerationMethods":["generateContent"]},{"name":"models/gemini-2.5-flash","supportedGenerationMethods":["generateContent"]}]})
        with patch.dict(os.environ,{"GEMINI_API_KEY":"test-only"},clear=True), patch('httpx.get',return_value=listing), patch('httpx.post',return_value=response({"candidates":[{"content":{"parts":[{"text":"Hello "},{"text":"student!"}]}}]})) as post:
            self.assertEqual(ns['_ai_reply']('system',[{'role':'teacher','text':'Hi'}]),'Hello student!')
            self.assertNotIn('tts',post.call_args.args[0])
            self.assertEqual(post.call_args.kwargs['json']['contents'][0]['role'],'user')
            self.assertLessEqual(post.call_args.kwargs['timeout'],8)
        # A configured but failing OpenAI provider must not suppress a working Gemini key.
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-only","GEMINI_API_KEY":"test-only"},clear=True), patch('httpx.post',side_effect=[response({'error':{}},429),response({'candidates':[{'content':{'parts':[{'text':'Recovered'}]}}]})]):
            self.assertEqual(ns['_ai_reply']('system',[{'role':'student','text':'Hi'}]),'Recovered')

if __name__ == '__main__': unittest.main()
