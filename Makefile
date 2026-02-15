DOCKER_IMAGE_LANGUAGE_REFERENCE:=language_reference

serve_falcon:
	./api.py \
		--path_static   static/ \
		--path_language language_reference/languages/ \
		--path_project  ~/code/personal/TeachProgramming/teachprogramming/static/projects/

build_all_local: clean
	# Projects are currently in a different repo and will be re-thought
	./api.py \
		--path_language language_reference/languages/ \
		--path_project  ~/code/personal/TeachProgramming/teachprogramming/static/projects/ \
 		--path_export   .

serve_build_local:
	python3 -m http.server

build_language_reference_local: clean
	./api.py \
		--path_language language_reference/languages/ \
 		--path_export   .

build_language_reference_docker: clean
	docker build --file build_language_reference.Dockerfile --tag ${DOCKER_IMAGE_LANGUAGE_REFERENCE} .
	docker create --name=${DOCKER_IMAGE_LANGUAGE_REFERENCE}_container ${DOCKER_IMAGE_LANGUAGE_REFERENCE}
	docker cp ${DOCKER_IMAGE_LANGUAGE_REFERENCE}_container:/app/api api/
	docker container rm ${DOCKER_IMAGE_LANGUAGE_REFERENCE}_container

clean:
	docker container rm ${DOCKER_IMAGE_LANGUAGE_REFERENCE}_container --force
	rm -rf api
