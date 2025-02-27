
auth_pool = [
        "0x9a3a97d1950356ef6d3c20acb5ab6699be454b1498ecd513bdc6d849497e42eb",
        "0x66ae71c0cc186692ff500c6d4b7dbe88059cd3fe506fe5b908a4bc9bca009fd6"
    ]

authorizer_hash =  "0x9a3a97d1950356ef6d3c20acb5ab6699be454b1498ecd513bdc6d849497e42eb"


def valid_report_fn( auth_pool, authorizer_hash):
    # report_auth_hash = Block.extrinsic.guarantees[0].report.authorizer_hash
    l = len(auth_pool)
    print(type(auth_pool))
    for i in auth_pool:
        # print(type(i),type(authorizer_hash))
        # print(i)
        # print(authorizer_hash)
        if i == authorizer_hash:
            return "case pass"

    return "Invalid work-package"

print(valid_report_fn(auth_pool, authorizer_hash))