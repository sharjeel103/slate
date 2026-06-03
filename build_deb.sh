#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Fixed default configurations
NAME="slate"
MAINTAINER="Sharjeel Ahmed <sharjeelarain0308@gmail.com>"
DESCRIPTION="A super lightweight, fast, and keyboard-driven PDF reader and annotator."
VERSION="1.0"

# If an argument is provided, treat it as the version number
if [[ "$#" -gt 0 ]]; then
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "Usage: ./build_deb.sh [version_number]"
        echo "Example: ./build_deb.sh 1.1"
        exit 0
    fi
    VERSION="$1"
fi

echo "=========================================="
echo " Building Debian Package: $NAME (v$VERSION) "
echo "=========================================="

# 1. Clean previous build folders
echo "Cleaning old build files..."
rm -rf build/ dist/ debian-build/ "${NAME}_"*_amd64.deb

# 2. Build executable using PyInstaller
echo "Running PyInstaller..."
./venv/bin/pyinstaller --noconfirm --onedir --windowed \
  --add-data "app/app_icon.png:app" \
  --name "$NAME" \
  main.py

# 3. Create Debian structure
echo "Assembling Debian package structure..."
mkdir -p debian-build/DEBIAN
mkdir -p debian-build/usr/bin
mkdir -p debian-build/usr/share/"$NAME"
mkdir -p debian-build/usr/share/applications
mkdir -p debian-build/usr/share/pixmaps

# Copy compiled files
cp -r dist/"$NAME"/* debian-build/usr/share/"$NAME"/
cp app/app_icon.png debian-build/usr/share/pixmaps/"$NAME".png

# Create startup script
cat << EOF > debian-build/usr/bin/"$NAME"
#!/bin/bash
exec /usr/share/$NAME/$NAME "\$@"
EOF
chmod +x debian-build/usr/bin/"$NAME"

# Create .desktop launcher
cat << EOF > debian-build/usr/share/applications/"$NAME".desktop
[Desktop Entry]
Name=Slate
Comment=Lightweight PDF Reader and Annotator
Exec=/usr/bin/$NAME %f
Icon=$NAME
Terminal=false
Type=Application
Categories=Office;Viewer;Graphics;
MimeType=application/pdf;
StartupNotify=true
EOF

# Create Debian control file
cat << EOF > debian-build/DEBIAN/control
Package: $NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Depends: libc6, libglib2.0-0, libxcb1, libx11-xcb1, libxkbcommon-x11-0, libdbus-1-3, libegl1, libfontconfig1
Maintainer: $MAINTAINER
Description: Slate PDF Annotator
 $DESCRIPTION
EOF

# 4. Build debian package
echo "Compiling .deb package..."
DEB_FILENAME="${NAME}_${VERSION}_amd64.deb"
dpkg-deb --build debian-build "$DEB_FILENAME"

echo ""
echo "Success! Package built: $DEB_FILENAME"
echo "=========================================="
