# Maintainer: Your Name <your.email@example.com>

pkgname=turnin
pkgver=1.0
pkgrel=1
pkgdesc="TurnIn App"
arch=('any')
url="https://github.com/yourusername/your-repo"
license=('MIT')
depends=('python-sshtunnel' 'python-paramiko' 'python-sentry-sdk' 'python-pyqt5' 'python-keyring' 'python-requests')

source=("$url/archive/v$pkgver.tar.gz")

build() {
  cd "$srcdir/your-repo-$pkgver"
  # No build actions are needed for a Python script
}

package() {
  cd "$srcdir/your-repo-$pkgver"
  
  # Install Python script
  install -Dm755 turnin.py "$pkgdir/usr/bin/turnin.py"

  install -Dm644 turnin.desktop "$pkgdir/usr/share/applications/turnin.desktop"
  
  # Install icons
  install -Dm644 cse.logo.png "$pkgdir/usr/share/icons/cse.logo.png"

  # Create desktop entry
  echo "[Desktop Entry]" > "$pkgdir/usr/share/applications/turnin.desktop"
  echo "Name=TurnIn" >> "$pkgdir/usr/share/applications/turnin.desktop"
  echo "Exec=python3 /usr/bin/turnin.py" >> "$pkgdir/usr/share/applications/turnin.desktop"
  echo "Icon=/usr/share/icons/cse.logo.png" >> "$pkgdir/usr/share/applications/turnin.desktop"
  echo "Type=Application" >> "$pkgdir/usr/share/applications/turnin.desktop"
}