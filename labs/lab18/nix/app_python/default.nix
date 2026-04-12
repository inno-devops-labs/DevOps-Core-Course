{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  
  src = ./.;
  
  propagatedBuildInputs = with pkgs.python3Packages; [
    flask
    prometheus-client
    psutil
    pyyaml
    python-json-logger
  ];
  
  format = "setuptools";
  
  preBuild = ''
    cat > setup.py << EOF
from setuptools import setup, find_packages

setup(
    name="devops-info-service",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "prometheus-client",
        "psutil",
        "pyyaml",
        "python-json-logger",
    ],
)
EOF
  '';
  
  doCheck = false;
  
  postInstall = ''
    mkdir -p $out/bin
    cat > $out/bin/devops-info-service <<EOF
    #!${pkgs.python3}/bin/python
    import sys
    import os
    
    sys.path.insert(0, '$out/${pkgs.python3.sitePackages}')
    
    from app import app
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 5050))
        app.run(host="0.0.0.0", port=port)
    EOF
    chmod +x $out/bin/devops-info-service
    
    if [ -f app.py ]; then
      cp app.py $out/${pkgs.python3.sitePackages}/
    fi
  '';
  
  meta = with pkgs.lib; {
    description = "DevOps Info Service - A Flask app with Prometheus metrics";
    license = licenses.mit;
    maintainers = [ "DevOps Student" ];
    platforms = platforms.all;
  };
}
