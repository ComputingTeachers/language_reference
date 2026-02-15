
serve_falcon:
	./api.py \
		--path_static   static/ \
		--path_language language_reference/languages/ \
		--path_project  ~/code/personal/TeachProgramming/teachprogramming/static/projects/

build:
	./api.py \
		--path_static   static/ \
		--path_language language_reference/languages/ \
		--path_project  ~/code/personal/TeachProgramming/teachprogramming/static/projects/ \
 		--export        .

serve:
	python3 -m http.server
