mkdir -p release/
rm stashofexile.zip
mv dist/cli.exe release/stashofexile.exe
cp -r assets/ release/
cd release/
zip -r ../stashofexile.zip .
cd ..
rm -rf release/
