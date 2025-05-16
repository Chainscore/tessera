curr_path = "tests/unit/execution/auth"

def test_read_authorizer():

		with open(curr_path + "/jam-null-authorizer.pvm", "rb") as f:
				print(f.read())
