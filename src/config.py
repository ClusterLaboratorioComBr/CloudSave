import json
from pathlib import Path
class Config:
    def __init__(self,conffile):
        self.dados = {}
        self.conffilepath = conffile
        self.conffile = Path(self.conffilepath)
        if ( self.conffile.exists() and self.conffile.is_file() ):
            self.dados = json.loads(open(self.conffilepath).read())
        else:
            # self.dados["purpose"] = "configfile"
            with open(self.conffilepath, 'w') as confsaida:
                json.dump(self.dados, confsaida)
            if (self.conffile.exists() and self.conffile.is_file()):
                self.dados = json.loads(open(self.conffilepath).read())
            else:
                print("Could not load json file " + conffile)
                exit(1)
    def atualizaJson(self,variavel,valor):
        self.dados[variavel] = valor
        with open(self.conffilepath, 'w') as confsaida:
            json.dump(self.dados,confsaida)
    def getDados(self,chave):
        return str(self.dados[chave])
    def getData(self,chave):
        return self.dados[chave]
    def delData(self,chave):
        del self.dados[chave]
        with open(self.conffilepath, 'w') as confsaida:
            json.dump(self.dados,confsaida)
