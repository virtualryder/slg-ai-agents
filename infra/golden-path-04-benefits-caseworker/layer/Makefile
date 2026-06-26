# SAM makefile build for the shared layer.
# Assembles platform_core + governance + agent core into the layer's python/ root,
# so every 311 Lambda imports them at runtime (no per-function vendoring).
build-SharedLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python"
	cp -r ../../../platform_core/slg_agent_platform "$(ARTIFACTS_DIR)/python/"
	cp -r ../../../governance "$(ARTIFACTS_DIR)/python/"
	cp ../../../aws-native-reference/04-benefits-caseworker/core.py "$(ARTIFACTS_DIR)/python/"
	# platform_core and governance are dependency-free by design; nothing to pip install.
