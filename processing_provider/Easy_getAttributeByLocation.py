# -*- coding: utf-8 -*-

"""
Easy_getAttributeByLocation.py
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
__author__ = 'Leandro França'
__date__ = '2021-01-08'
__copyright__ = '(C) 2021, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *
import processing
from lftools.geocapt.imgs import Imgs
import os
from qgis.PyQt.QtGui import QIcon


class GetAttributeByLocation(QgsProcessingAlgorithm):

    LOC = QgsApplication.locale()[:2]

    def translate(self, string):
        return QCoreApplication.translate('Processing', string)

    def tr(self, *string):
        # Traduzir para o portugês: arg[0] - english (translate), arg[1] - português
        if self.LOC == 'pt':
            if len(string) == 2:
                return string[1]
            else:
                return self.translate(string[0])
        else:
            return self.translate(string[0])

    def createInstance(self):
        return GetAttributeByLocation()

    def name(self):
        return 'getattributebylocation'

    def displayName(self):
        return self.tr('Get attribute by location', 'Pegar atributo pela localização')

    def group(self):
        return self.tr('Easy', 'Mão na Roda')

    def groupId(self):
        return 'easy'

    def tags(self):
        return self.tr('easy,topologia,centroide,quadra,lote,parcel,setor,cadastro,cadastre,parcela,polígono').split(',')

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images/easy.png'))

    txt_en = '''This algorithm fills in the attributes of a specific field from another layer, in such a way that the feature's centroid intercepts the corresponding feature from the other layer.
The source and destination fields must be indicated to fill in the attributes.'''
    txt_pt = '''Este algoritmo preenche os atributos de um campo específico a partir de outra camada, tal que o centróide da feição intercepte a feição correspondente da outra camada.
Os campos de origem e de destino devem ser indicadas para preenchimento dos atributos.'''
    figure = 'images/tutorial/easy_get_attributes.jpg'

    SOURCE ='SOURCE'
    SOURCE_FIELD = 'SOURCE_FIELD'
    DEST = 'DEST'
    DEST_FIELD = 'DEST_FIELD'
    TOPOLOGY = 'TOPOLOGY'
    SAVE = 'SAVE'

    def shortHelpString(self):
        social_BW = Imgs().social_BW
        footer = '''<div align="center">
                      <img src="'''+ os.path.join(os.path.dirname(os.path.dirname(__file__)), self.figure) +'''">
                      </div>
                      <div align="right">
                      <p align="right">
                      <b>'''+self.tr('Author: Leandro Franca', 'Autor: Leandro França')+'''</b>
                      </p>'''+ social_BW + '''</div>
                    </div>'''
        return self.tr(self.txt_en, self.txt_pt) + footer

    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SOURCE,
                self.tr('Attribute source layer', 'Camada fonte de atributo'),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELD,
                self.tr('Source field', 'Campo de origem'),
                parentLayerParameterName=self.SOURCE
            )
        )

        self.addParameter(
        QgsProcessingParameterVectorLayer(
            self.DEST,
            self.tr('Target layer for attribute', 'Camada de destino para o atributo'),
            [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.DEST_FIELD,
                self.tr('Destination field', 'Campo de destino'),
                parentLayerParameterName=self.DEST
            )
        )

        tipos = [self.tr('from target feature','da feição alvo'),
                 self.tr('from origin feature','da feição de origem'),
               ]

        self.addParameter(
            QgsProcessingParameterEnum(
                self.TOPOLOGY,
                self.tr('Intersection with the centroid (Topology)', 'Interseção com o centróide (Topologia)'),
				options = tipos,
                defaultValue= 0
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE,
                self.tr('Save Editions', 'Salvar Edições'),
                defaultValue=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        lotes = self.parameterAsVectorLayer(
            parameters,
            self.SOURCE,
            context
        )
        if lotes is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.SOURCE))

        campo_lote = self.parameterAsFields(
            parameters,
            self.SOURCE_FIELD,
            context
        )
        if campo_lote is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.SOURCE_FIELD))

        edif = self.parameterAsVectorLayer(
            parameters,
            self.DEST,
            context
        )
        if edif is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.DEST))

        campo_edif = self.parameterAsFields(
            parameters,
            self.DEST_FIELD,
            context
        )
        if campo_edif is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.DEST_FIELD))

        columnIndex = edif.fields().indexFromName(campo_edif[0])
        att = campo_lote[0]
        edif.startEditing()

        topologia = self.parameterAsEnum(
            parameters,
            self.TOPOLOGY,
            context
        )

        feedback.pushInfo(self.tr('Source field: {}'.format(campo_lote[0]), 'Campo de origem: {}'.format(campo_lote[0])))
        feedback.pushInfo(self.tr('Destination field: {}'.format(campo_edif[0]), 'Campo de destino: {}\n'.format(campo_edif[0])))

        produto = edif.featureCount()*lotes.featureCount()
        total = 100.0 /produto if produto else 0
        cont = 0
        if topologia == 0:
            for feat1 in edif.getFeatures():
                centroide = feat1.geometry().centroid()
                for feat2 in lotes.getFeatures():
                    if centroide.intersects(feat2.geometry()):
                        valor = feat2[att]
                        edif.changeAttributeValue(feat1.id(), columnIndex, valor)
                        break
                    cont += 1
                    if feedback.isCanceled():
                        break
                    feedback.setProgress(int(cont * total))
        elif topologia == 1:
            for feat1 in lotes.getFeatures():
                centroide = feat1.geometry().centroid()
                valor = feat1[att]
                for feat2 in edif.getFeatures():
                    if centroide.intersects(feat2.geometry()):
                        edif.changeAttributeValue(feat2.id(), columnIndex, valor)
                        break
                    cont += 1
                    if feedback.isCanceled():
                        break
                    feedback.setProgress(int(cont * total))

        salvar = self.parameterAsBool(
            parameters,
            self.SAVE,
            context
        )
        if salvar is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.SAVE))

        if salvar:
            edif.commitChanges() # salva as edições

        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo(self.tr('Leandro Franca - Cartographic Engineer', 'Leandro França - Eng Cart'))

        return {}
