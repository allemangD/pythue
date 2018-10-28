import thue.parser


def main():
    with open('testing.ret') as f:
        src = f.read()

    pgm = thue.parser.compile(src)
    res = pgm.run()
    print(res)


if __name__ == '__main__':
    main()
