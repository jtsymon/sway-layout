pkgname=sway-layout
pkgver=r12.7b116c0
pkgrel=1
pkgdesc='Start and automatically layout applications in sway'
license=('GPL2')
arch=(any)
depends=('python-i3ipc')
makedepends=('git')
url='https://github.com/jtsymon/sway-layout'
source=("git+$url.git")
md5sums=('SKIP')

pkgver() {
  cd "$_gitname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
        cd "${srcdir}/${pkgname}"
        install -D -m755 "./sway-layout.py" "${pkgdir}/usr/bin/sway-layout"
}
