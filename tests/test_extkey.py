from binascii import unhexlify
from pytest import raises
from typing import List
from secp256k1 import Secp256k1, FLAG_ALL
from grin.extkey import ChildNumber, ReferenceHasher, ExtendedSecretKey, ExtendedPublicKey, HardenedIndexError
from grin.util import base58_encode, base58check_encode, base58_decode, base58check_decode


def test_base58_encode():
    assert base58_encode(bytearray([0])) == b"1"
    assert base58_encode(bytearray([1])) == b"2"
    assert base58_encode(bytearray([58])) == b"21"
    assert base58_encode(bytearray([13, 36])) == b"211"
    assert base58_encode(bytearray([0, 13, 36])) == b"1211"
    assert base58_encode(bytearray([0, 0, 0, 0, 13, 36])) == b"1111211"
    assert base58check_encode(bytearray(unhexlify(b"00f8917303bfa8ef24f292e8fa1419b20460ba064d"))) \
        == b"1PfJpZsjreyVrqeoAfabrRwwjQyoSQMmHH"


def test_base58_decode():
    assert base58_decode(b"1") == bytearray([0])
    assert base58_decode(b"2") == bytearray([1])
    assert base58_decode(b"21") == bytearray([58])
    assert base58_decode(b"211") == bytearray([13, 36])
    assert base58_decode(b"1211") == bytearray([0, 13, 36])
    assert base58_decode(b"111211") == bytearray([0, 0, 0, 13, 36])
    assert base58check_decode(b"1PfJpZsjreyVrqeoAfabrRwwjQyoSQMmHH") \
        == bytearray(unhexlify(b"00f8917303bfa8ef24f292e8fa1419b20460ba064d"))


def test_base58_roundtrip():
    s = b"xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs"
    v = base58check_decode(s)
    assert base58check_encode(v) == s
    assert base58check_decode(base58check_encode(v)) == v


def check_path(secp: Secp256k1, seed: bytearray, path: List[ChildNumber],
               expected_secret: bytes, expected_public: bytes):
    hasher = ReferenceHasher()
    secret = ExtendedSecretKey.new_master(secp, hasher, seed)
    public = ExtendedPublicKey.from_secret(secp, hasher, secret)
    assert secret.derive_secret(secp, hasher, path).to_base58check() == expected_secret

    hardened = False
    for i in path:
        if i.is_hardened():
            hardened = True
            break

    # This should fail if any of the indices are hardened
    if hardened:
        with raises(HardenedIndexError):
            public.derive_public(secp, hasher, path)
    else:
        assert public.derive_public(secp, hasher, path).to_base58check(secp) == expected_public

    # Check keys at each step of the path
    for i in path:
        secret = secret.ckd_secret(secp, hasher, i)
        if i.is_normal():
            public2 = public.ckd_public(secp, hasher, i)
            public = ExtendedPublicKey.from_secret(secp, hasher, secret)
            assert public == public2
        else:
            with raises(HardenedIndexError):
                public.ckd_public(secp, hasher, i)
            public = ExtendedPublicKey.from_secret(secp, hasher, secret)

    # Test serialization
    assert secret.to_base58check() == expected_secret
    assert public.to_base58check(secp) == expected_public

    # Test deserialization
    assert secret == ExtendedSecretKey.from_base58check(secp, expected_secret)
    # assert public == ExtendedPublicKey.from_base58check(secp, expected_public)


def test_path_1():
    secp = Secp256k1(None, FLAG_ALL)
    seed = bytearray(unhexlify(b"000102030405060708090a0b0c0d0e0f"))

    # m
    check_path(secp, seed, [],
               b"xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi",
               b"xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8")

    # m/0h
    check_path(secp, seed, [ChildNumber.from_hardened_index(0)],
               b"xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7",
               b"xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw")

    # m/0h/1
    check_path(secp, seed, [ChildNumber.from_hardened_index(0), ChildNumber.from_normal_index(1)],
               b"xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs",
               b"xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ")

    # m/0h/1/2h
    check_path(secp, seed, [ChildNumber.from_hardened_index(0), ChildNumber.from_normal_index(1),
                            ChildNumber.from_hardened_index(2)],
               b"xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM",
               b"xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5")

    # m/0h/1/2h/2
    check_path(secp, seed, [ChildNumber.from_hardened_index(0), ChildNumber.from_normal_index(1),
                            ChildNumber.from_hardened_index(2), ChildNumber.from_normal_index(2)],
               b"xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334",
               b"xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV")

    # m/0h/1/2h/2/1000000000
    check_path(secp, seed, [ChildNumber.from_hardened_index(0), ChildNumber.from_normal_index(1),
                            ChildNumber.from_hardened_index(2), ChildNumber.from_normal_index(2),
                            ChildNumber.from_normal_index(1000000000)],
               b"xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76",
               b"xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy")


def test_path_2():
    secp = Secp256k1(None, FLAG_ALL)
    seed = bytearray(unhexlify(b"fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"))

    # m
    check_path(secp, seed, [],
               b"xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U",
               b"xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB")

    # m/0
    check_path(secp, seed, [ChildNumber.from_normal_index(0)],
               b"xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt",
               b"xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH")

    # m/0/2147483647h
    check_path(secp, seed, [ChildNumber.from_normal_index(0), ChildNumber.from_hardened_index(2147483647)],
               b"xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9",
               b"xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a")

    # m/0/2147483647h/1
    check_path(secp, seed, [ChildNumber.from_normal_index(0), ChildNumber.from_hardened_index(2147483647),
                            ChildNumber.from_normal_index(1)],
               b"xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef",
               b"xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon")

    # m/0/2147483647h/1/2147483646h
    check_path(secp, seed, [ChildNumber.from_normal_index(0), ChildNumber.from_hardened_index(2147483647),
                            ChildNumber.from_normal_index(1), ChildNumber.from_hardened_index(2147483646)],
               b"xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc",
               b"xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL")

    # m/0/2147483647h/1/2147483646h/2
    check_path(secp, seed, [ChildNumber.from_normal_index(0), ChildNumber.from_hardened_index(2147483647),
                            ChildNumber.from_normal_index(1), ChildNumber.from_hardened_index(2147483646),
                            ChildNumber.from_normal_index(2)],
               b"xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j",
               b"xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt")


def test_path_3():
    secp = Secp256k1(None, FLAG_ALL)
    seed = bytearray(unhexlify(b"4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be"))

    # m
    check_path(secp, seed, [],
               b"xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6",
               b"xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13")

    # m/0h
    check_path(secp, seed, [ChildNumber.from_hardened_index(0)],
               b"xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L",
               b"xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y")
