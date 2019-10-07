class rainbow:
    def clear(self):
        print('rainbow.clear')

    def set_pixel(self, a, b, c, d, e):
        print('rainbow.set_pixel')

    def show(self):
        print('rainbow.show')


class display:
    def print_str(self, s):
        print('display.print_str %s' % s)

    def show(self):
        print('display.show')

    def set_decimal(self):
        print('display.set_decimal')
