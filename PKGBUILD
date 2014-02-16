# Maintainer: Kenneth Henderick <kenneth@ketronic.be>
pkgname=zfs-snap-manager
pkgver=0.1.4
pkgrel=1
pkgdesc="A bunch of python2 scripts running as a service, using a configuration file to manage ZFS snapshots"
arch=('any')
url="https://github.com/khenderick/zfs-snap-manager"
license=('MIT')
depends=('zfs' 'python2>=2.7' 'openssh' 'mbuffer' 'python2-daemon')
makedepends=('git')
backup=('etc/zfssnapmanager.cfg')

_gitroot="git://github.com/khenderick/zfs-snap-manager.git"
_gitname="zfs-snap-manager"

build() {
    if [ -d "$srcdir/$_gitname" ]; then
		cd $_gitname && git pull origin
		msg "The local files are updated."
	else
		git clone $_gitroot $_gitname
		cd $_gitname
	fi
}

package() {
    cd $_gitname
    mkdir -p "$pkgdir/usr/lib/zfs-snap-manager/"
    install -D -m644 "scripts/clean.py" "$pkgdir/usr/lib/zfs-snap-manager/clean.py"
    install -D -m644 "scripts/zfs.py" "$pkgdir/usr/lib/zfs-snap-manager/zfs.py"
    install -D -m644 "scripts/toolbox.py" "$pkgdir/usr/lib/zfs-snap-manager/toolbox.py"
    install -D -m755 "scripts/manager.py" "$pkgdir/usr/lib/zfs-snap-manager/manager.py"
    install -D -m644 "LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -D -m644 "system/zfs-snap-manager.service" "${pkgdir}/usr/lib/systemd/system/zfs-snap-manager.service"
}
