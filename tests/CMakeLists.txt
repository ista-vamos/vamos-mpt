add_test(NAME prefixexpr-parsing
	 COMMAND python ./prefixexpr.py)

add_test(NAME prefixexpr-derivatives
	 COMMAND python ./derivs.py)

add_test(NAME prefixexpr-transducers
	 COMMAND python ./pet.py)
