"""
Ce script permet de générer une fiche bibliographique d'un ouvrage en récupérant des informations à partir de son code ISBN.

Pour utiliser

Taper
'python generateurFicheBibilio.py'

Puis le code ISBN de l'ouvrage à rechercher, par exemple :
2362316343 pour obtenir 'Les Loups-Garous de Thiercelieux : Lune rousse'

"""

#importation des libraries nécessaires

import pandas as pd
from bs4 import BeautifulSoup as bs
import urllib.request
from urllib.request import urlopen
import os
import time
import json
from datetime import datetime
from fuzzywuzzy import fuzz,utils
import copy
from difflib import SequenceMatcher
from datetime import datetime

# Creation des dossiers utiles au stockage des fiches et image:

def creer_dossier(dossier):
    script_directory = os.path.dirname(os.path.realpath(__file__))
    parentDirectory = os.path.dirname(script_directory)
    chemin_nouveau_dossier = os.path.join(parentDirectory, dossier)

# Vérifier si le dossier existe déjà
    if not os.path.exists(chemin_nouveau_dossier):
    # Créer le dossier
        os.mkdir(chemin_nouveau_dossier)




# Definition de la fonction pour creer les fiche json

def creer_fiche(ISBN,dossier,fiche):
    absolutepath = os.path.abspath(__file__)
    fileDirectory = os.path.dirname(absolutepath)
    parentDirectory = os.path.dirname(fileDirectory)
    newPath = os.path.join(parentDirectory, dossier)   
    jsonString = json.dumps(fiche)
    jsonFile = open(newPath+'\ '+ ISBN +".json", "w")
    jsonFile.write(jsonString)
    jsonFile.close() 




# Definition des fonctions pour l'extraction Amazon
# En entrée le code ISBN et en sortie une fiche complétée avec les informations disponibles sur Amazon
def extraction_amazon(entree:str):
    ISBN = ""
    ISBN=entree.replace(" ","").replace("-","")


    if len(ISBN)==10:
        url = "https://www.amazon.fr/dp/"+ISBN
    elif len(ISBN)==13:
        url1="https://www.amazon.fr/s?k="+ISBN
        try:
            recherche=urllib.request.urlopen(url1,timeout=100000)
            soup1=bs(recherche)
            link =str(soup1.find('a', {'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})['href'])
            indice = link.find("/dp/")
            url="https://www.amazon.fr"+link[indice:]
        except:
            raise FileNotFoundError("Une erreur s'est produite veuillez vérifier votre connexion Internet et rééssayer")
            

    else:
        raise SyntaxError("Erreur dans le format du code ISBN")


    try:
        page=urllib.request.urlopen(url,timeout=100000)
        soup2=bs(page,features="html.parser")
    except:
        raise FileNotFoundError("Une erreur s'est produite veuillez vérifier votre connexion Internet et rééssayer")

    fiche={"isbn10":"","isbn13":"","titre":"","sousTitre":"","editeur":"","auteurs":"","fonctions":"","date":"","genre":"","nbPages":"","poids":0.0,"prix":0.0,"image":"","format":"","collection":"","numeroCollection":0,"serie":"","numeroSerie":0,"reliure":"","consultation":"","creation":""}
    if len(ISBN)==13:
        fiche["isbn13"]=ISBN
    elif len(ISBN)==10:
        fiche["isbn10"]=ISBN

    try:
        titre = soup2.find('span', {'id': 'productTitle'}).text
        fiche["titre"]=titre.strip()
    except:
        pass

    try:
        auteurs=soup2.find_all('span', {'class': 'author notFaded'})
        a=[]
        f=[]
        for auteur in auteurs:
            auteur=auteur.text.replace("\n","").replace(",","")
            a.append(auteur[:auteur.find(" (")])
            f.append(auteur[auteur.find("(")+1:auteur.find(")")])
        fiche["auteurs"]=a
        fiche["fonctions"]=f
    except:
        pass


    try:   
        poids=soup2.find('ul',{'class': 'a-unordered-list a-nostyle a-vertical a-spacing-none detail-bullet-list'})
        for attribut in poids:
            attribut=attribut.text.replace("  ","").replace("\n","")
            if attribut[:8]==" Éditeur":
                fiche["editeur"]=attribut[attribut.find(":")+1:attribut.find("(")]
                fiche["editeur"]=fiche["editeur"].replace("\u200e","").strip()
                fiche["date"]=attribut[attribut.find("(")+1:attribut.find(")")].strip()
            elif attribut[:6]==" Poche":
                fiche["reliure"]="Broché"
                fiche["nbPages"]=attribut[attribut.find(":")+1:attribut.find("pages")]
                fiche["nbPages"]=int(fiche["nbPages"].replace("\u200e",""))
            elif attribut[:7]==" Broché":
                fiche["reliure"]="Broché"
                fiche["nbPages"]=attribut[attribut.find(":")+1:attribut.find("pages")]
                fiche["nbPages"]=int(fiche["nbPages"].replace("\u200e",""))
            elif attribut[:6]==" Relié":
                fiche["reliure"]=" Relié"
                fiche["nbPages"]=attribut[attribut.find(":")+1:attribut.find("pages")]
                fiche["nbPages"]=int(fiche["nbPages"].replace("\u200e",""))

            elif attribut[:19]==" Poids de l'article":
                if attribut[-3:]==" g ":
                    fiche["poids"]=attribut[attribut.find(":")+1:attribut.find("g")]
                    fiche["poids"]=float(fiche["poids"].replace("\u200e",""))
                elif attribut[-3:]=="kg ":
                    fiche["poids"]=attribut[attribut.find(":")+1:attribut.find("kg")]
                    fiche["poids"]=float(fiche["poids"].replace("\u200e",""))*1000

            elif attribut[:11]==" Dimensions":
                fiche["format"]=attribut[attribut.find(":")+1:attribut.find("cm")+2]
                fiche["format"]=(fiche["format"].replace("\u200e","").strip())
    except:
        pass
            

    try:
        prix=soup2.find('span', {'class': 'a-offscreen'})
        fiche["prix"]=prix.text[:-1].replace(",",".").strip()
        fiche["prix"]=float(fiche["prix"].replace("\xa0",""))
    except:
        pass

    try:
        serie=soup2.find('div', {'id': 'rpi-attribute-book_details-series'}) 
        serie=serie.text
        if serie[:7]=="  Fait ":
            serie_nom=serie[serie.find("    ")+5:]
            fiche["serie"]=serie_nom.strip()
        elif serie[:7]=="  Livre":
            numero=serie[serie.find("Livre")+5:serie.find("sur")]
            serie_nom=serie[serie.find("    ")+5:]
            fiche["numeroSerie"]=int(numero)
            fiche["serie"]=serie_nom.strip()
    except:
        pass

    try:
        lien=soup2.find('div', {'id': 'booksImageBlock_feature_div'})
        lien=lien.find('img',{'class': 'a-dynamic-image image-stretch-vertical frontImage'})["data-a-dynamic-image"]
        lien=lien[lien.find('"')+1:lien.find('":')]
    except:
        pass


    try:
        absolutepath = os.path.abspath(__file__)
        fileDirectory = os.path.dirname(absolutepath)
        parentDirectory = os.path.dirname(fileDirectory)
        newPath = os.path.join(parentDirectory, 'couverture')
        urllib.request.urlretrieve(lien, newPath+'\ '+ ISBN +".jpg")
    except:
        print("Problème de récupération de l'image")

    fiche["image"]=newPath+'\ '+ ISBN +".jpg"

    fiche["consultation"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    creer_fiche(entree,'fiche_amazon',fiche)
    return(fiche)


# Definition des fonctions pour l'extraction Google Books
# Fonction globale permettant d'obtenir une fiche completee avec les informations sur Google Books avec le code ISBN en entree

def extraction_google(entree:str):
    ISBN = ""
    ISBN=entree.replace(" ","").replace("-","")

    fiche_google= extract(get_book_raw(ISBN))
    creer_fiche(entree,'fiche_google',fiche_google)
    return fiche_google
# fonction donne a partir d'un ISBN un dictionnaire contenant les informations donnees par l'API de Google Books
def get_book_raw(code):
    #variables de départ : url "vide" et isbn
    api = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
    isbn = code.strip()

    #recuperer la reponse serveur http liee a l'isbn demande
    reponse = urlopen(api + isbn)
    #extraire les données du json de la reponse, et les charger dans un dictionnaire python
    book_data = json.load(reponse)
    infos=book_data['items'][0]['volumeInfo']
    return(infos)

# fonction en entree un dictionnaire python et redonne la fiche completee des informations disponibles de cette fiche
def extract(raw):
    data = {"isbn10"           :"",
             "isbn13"           :"",
             "titre"            :"",
             "sousTitre"        :"",
             "editeur"          :"",
             "auteurs"          :"",
             "fonctions"        :"",
             "date"             :"",
             "genre"            :"",
             "nbPages"          :"",
             "poids"            :0.0,
             "prix"             :0.0,
             "image"            :"",
             "format"           :"",
             "collection"       :"",
             "numeroCollection" :0,
             "serie"            :"",
             "numeroSerie"      :0,
             "reliure"          :"",
             "consultation"     :"",
             "creation"         :""}
    data['isbn10'] = raw.get('industryIdentifiers')[0]['identifier']
    data['isbn13'] = raw.get('industryIdentifiers')[1]['identifier']
    data['titre'] = raw.get('title')
    data['sousTitre'] = raw.get('subtitle')
    data['auteurs'] = raw.get('authors')
    data['editeur'] = raw.get('publisher')
    date_str = raw.get('publishedDate')
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    data['date'] = date_obj.strftime("%d %B %Y")
    data['nbPages'] = int(raw.get('pageCount'))
    data['genre'] = raw.get('categories')
    data['consultation'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data



# definition des fonctions d'aggregation:
#fonction qui compare 2 arguments et definie si elles sont equivalentes ou non
def est_equivalent(attribut1,attribut2):
    if type(attribut1)==str:
        if fuzz.partial_ratio(utils.full_process(attribut1),utils.full_process(attribut2))>75:
            return True
    else:
        return attribut1==attribut2
# fonction qui a partir d'une liste d'attribut va rendre une nouvelle liste sans les attributs qui sont equivalents a d'autres
def sont_equivalents(attribut:list):
    new_attribut=copy.deepcopy(attribut)
    for i in range(len(attribut)):
        for j in range(len(attribut)):
            if i<j:
                if est_equivalent(attribut[i],attribut[j]):
                    if type(attribut[i])==str:
                        if len(attribut[i])<=len(attribut[j]):
                            try:
                                new_attribut.remove(attribut[i])
                            except:
                                pass
                        else:
                            try:
                                new_attribut.remove(attribut[j])
                            except:
                                pass
                    else:
                        try:
                            new_attribut.remove(attribut[j])
                        except:
                            pass
    return new_attribut
# fonction qui va permettre d'agreger des fiches 
def aggregation(sources:dict,priorite:dict,entree:str):
    final = {"isbn10":"","isbn13":"","titre":"","sousTitre":"","editeur":"","auteurs":"","fonctions":"","date":"","genre":"","nbPages":"","poids":0.0,"prix":0.0,"image":"","format":"","collection":"","numeroCollection":0,"serie":"","numeroSerie":0,"reliure":"","consultation":"","creation":""}
    for key in final:
        # Si on décide qu'une source a des priorités sur d'autres et que de plus elle soit rempli
        if priorite[key]!="" and (sources[priorite[key]][key]!="" or sources[priorite[key]][key]!=0):
            final[key]=sources[priorite[key]][key]
        else:
            attribut = []
            for source in sources:
                # Regarder si les attributs sont nuls et s'il en reste 1 
                if sources[source][key]!= "" and sources[source][key]!=0 and  sources[source][key]!= None:
                    attribut.append(sources[source][key])
            if len(attribut)==1:
                final[key]=attribut[0]
            elif len(attribut)>1:
                #On regarde si les attributs sont équivalents
                attribut=sont_equivalents(attribut)
                if len(attribut)==1:
                    # s'il en reste 1 on le choisi
                    final[key]=attribut[0]
                else:
                    #sinon on demande à l'utilisateur de choisir quel argument il choisit
                    print("Collision pour l'entrée " + key)
                    for i in range(len(attribut)):
                        print("Choix",i,":",attribut[i])
                    choice = -1
                    while (not (choice in list(range(len(attribut))))):
                        choice = int(input("Donner le numéro voulu "))
                        if (not (choice in list(range(len(attribut))))):
                            print("Valeur incorrecte")
                    final[key]=attribut[choice]
    final["creation"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    creer_fiche(entree,'fiche_agregee',final)
    return final


creer_dossier('fiche_google')
creer_dossier('couverture')
creer_dossier('fiche_amazon')
creer_dossier('fiche_agregee')

while True:
    entree=input("Appuyez sur Entrée pour quitter... ou donner le code ISBN ")
    if entree =="":
        break
    fiche_amazon={"isbn10":"","isbn13":"","titre":"","sousTitre":"","editeur":"","auteurs":"","fonctions":"","date":"","genre":"","nbPages":"","poids":0.0,"prix":0.0,"image":"","format":"","collection":"","numeroCollection":0,"serie":"","numeroSerie":0,"reliure":"","consultation":"","creation":""}
    fiche_google={"isbn10":"","isbn13":"","titre":"","sousTitre":"","editeur":"","auteurs":"","fonctions":"","date":"","genre":"","nbPages":"","poids":0.0,"prix":0.0,"image":"","format":"","collection":"","numeroCollection":0,"serie":"","numeroSerie":0,"reliure":"","consultation":"","creation":""}
    try:
        fiche_amazon=extraction_amazon(entree)
    except Exception as e :
        print("Erreur: ",str(e))
    try:
        fiche_google=extraction_google(entree)
    except Exception as e:
        print("Erreur: ",str(e))
    priorite = {"isbn10"            :"",
                "isbn13"            :"",
                "titre"             :"",
                "sousTitre"         :"",
                "editeur"           :"",
                "auteurs"           :"amazon",
                "fonctions"         :"amazon",
                "date"              :"",
                "genre"             :"",
                "nbPages"           :"",
                "poids"             :"",
                "prix"              :"",
                "image"             :"amazon",
                "format"            :"",
                "collection"        :"",
                "numeroCollection"  :"",
                "serie"             :"",
                "numeroSerie"       :"",
                "reliure"           :"",
                "consultation"      :"",
                "creation"          :""
                }
    sources={"amazon":fiche_amazon,"google":fiche_google}
    fiche_aggrege=aggregation(sources,priorite,entree)
    print(fiche_aggrege)
    fiche_test={"isbn10":"","isbn13":"","titre":"","sousTitre":"","editeur":"","auteurs":"","fonctions":"","date":"","genre":"","nbPages":"","poids":0.0,"prix":0.0,"image":"","format":"","collection":"","numeroCollection":0,"serie":"","numeroSerie":0,"reliure":"","consultation":"","creation":""}
    exhaustivite = 0 
    critere_source = 0
    for key in fiche_test:
        if fiche_test[key]!=fiche_aggrege[key]:
            exhaustivite+=1
    print("Critere d'exhaustivite: "+str(exhaustivite)+"/21")
    if fiche_test!=fiche_amazon:
        critere_source +=1
    else:
        print("Source Amazon manquante")
    if fiche_test!=fiche_google:
        critere_source +=1
    else:
        print("Source Google Books manquante")
    print("Critere de croisement des sources: "+str(critere_source)+"/2")
