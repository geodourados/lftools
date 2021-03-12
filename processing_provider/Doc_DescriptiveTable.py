# -*- coding: utf-8 -*-

"""
***************************************************************************
    Doc_DescriptiveTable.py
    ---------------------
    Date                 : Jul 10
    Copyright            : (C) 2020 by Leandro França
    Email                : geoleandro.franca@gmail.com
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
__date__ = 'Jul 10'
__copyright__ = '(C) 2020, Leandro França'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsApplication,
                       QgsProject,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)

import os
from math import pi, sqrt
from lftools.geocapt.imgs import Imgs
from lftools.geocapt.cartography import MeridianConvergence, SRC_Projeto
from lftools.geocapt.topogeo import azimute, dd2dms, str2HTML
from qgis.PyQt.QtGui import QIcon

class DescriptiveTable(QgsProcessingAlgorithm):

    LOC = QgsApplication.locale()

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
        return DescriptiveTable()

    def name(self):
        return 'descriptivetable'

    def displayName(self):
        return self.tr('Descriptive table of vertices and sides', 'Memorial Sintético')

    def group(self):
        return self.tr('Documents', 'Documentos')

    def groupId(self):
        return 'documents'

    def tags(self):
        return self.tr('monograph,table,geodetic,descriptive,syntetic,memorial,property,topography,survey,real,estate,georreferencing,plan,cadastral,cadastre,documnt').split(',')

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images/document.png'))

    def shortHelpString(self):
        txt_en = 'This tool generates the Descriptive Table of Vertices and Sides, also known as Synthetic Descriptive Memorial, from a layer of points with the attributes of code and order (sequence) of the points.'
        txt_pt = 'Esta ferramenta gera a Tabela Descriva de Vértices e Lados, também conhecida como Memorial Descritivo Sintético, a partir de uma camada de pontos com os atributos de código e ordem (sequência) dos pontos.'
        social_BW = Imgs().social_BW
        footer = '''<div align="center">
                      <img src="'''+ os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images/tutorial/doc_descriptive_table.jpg') +'''">
                      </div>
                      <div align="right">
                      <div>''' + self.tr('This tool works properly only with data in "topogeo" modeling.',
                                         'Esta ferramenta funciona adequadamente com os dados na modelagem "topogeo".') + '''
                      </div>
                      <p align="right">
                      <b><a href="https://www.researchgate.net/publication/346925730_PROPOSICAO_METODOLOGICA_COM_EMPREGO_DE_SOFTWARE_LIVRE_PARA_A_ELABORACAO_DE_DOCUMENTOS_DE_LEVANTAMENTO_TOPOGRAFICO_DE_IMOVEIS_DA_UNIAO_Methodological_proposition_with_the_use_of_free_software_for_the_p" target="_blank">'''+self.tr('Click here for more informations!',
                                    'Clique aqui para saber mais sobre essa modelagem!') +'</a><br><br>'+ self.tr('Author: Leandro Franca', 'Autor: Leandro França')+'''</b>
                      </p>'''+ social_BW + '''</div>
                    </div>'''
        return self.tr(txt_en, txt_pt) + footer

    PONTOS = 'PONTOS'
    HTML = 'HTML'
    INICIO = 'INICIO'
    FIM = 'FIM'
    TITULO = 'TITULO'
    FONTSIZE = 'FONTSIZE'

    def initAlgorithm(self, config=None):

        # 'INPUTS'
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PONTOS,
                self.tr('Boundary Survey Points', 'Pontos de Limite'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.INICIO,
                self.tr('First vertex', 'Primeiro vértice'),
                type =0,
                defaultValue = 1
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.FIM,
                self.tr('Last vertex', 'Último vértice'),
                type =0,
                defaultValue = -1
                )
            )

        self.addParameter(
            QgsProcessingParameterString(
                self.TITULO,
                self.tr('Title', 'Título'),
                defaultValue = self.tr("SOMEONE'S PROPERTY", 'IMÓVEL DE ALGUÉM')
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.FONTSIZE,
                self.tr('Font size', 'Tamanho da fonte'),
                type =0,
                defaultValue = 12
                )
            )

        # 'OUTPUTS'
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.HTML,
                self.tr('Descriptive table', 'Memorial Sintético'),
                self.tr('HTML files (*.html)')
            )
        )


    def processAlgorithm(self, parameters, context, feedback):

        vertices = self.parameterAsSource(parameters,
                                                     self.PONTOS,
                                                     context)

        if vertices is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.PONTOS))

        ini = self.parameterAsInt(
            parameters,
            self.INICIO,
            context
        )
        if ini is None or ini<1:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INICIO))

        fim = self.parameterAsInt(
            parameters,
            self.FIM,
            context
        )
        if fim is None or fim==0 or fim<-1:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIM))
        if fim !=-1:
            if fim < ini:
                raise QgsProcessingException(self.invalidSourceError(parameters, self.FIM))

        titulo = self.parameterAsString(parameters,
                                         self.TITULO,
                                         context)
        if titulo is None:
            titulo = ''
        if not titulo in ['',' ']:
            titulo = ' - ' + titulo

        fontsize = self.parameterAsInt(
            parameters,
            self.FONTSIZE,
            context
        )
        if fontsize is None or ini<1:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FONTSIZE))

        # Pegando o SRC do Projeto
        SRC = QgsProject.instance().crs().description()
        # Verificando o SRC
        if QgsProject.instance().crs().isGeographic():
            raise QgsProcessingException(self.tr('The Project CRS must be projected!', 'O SRC do Projeto deve ser Projetado!'))
        feedback.pushInfo(self.tr('Project CRS is {}.', 'SRC do Projeto é {}.').format(SRC))

        # Validando dados de entrada
        # ponto_limite
        ordem_list = list(range(1,vertices.featureCount()+1))
        ordem_comp = []
        for feat in vertices.getFeatures():
            ordem_comp += [feat['ordem']]
            codigo_item = feat['codigo']
            if not codigo_item or codigo_item in ['', ' ']:
                raise QgsProcessingException(self.tr('The code attribute must be filled in for all features!', 'O atributo código deve ser preenchido para todas as feições!'))
        ordem_comp.sort()
        if ordem_list != ordem_comp:
            raise QgsProcessingException(self.tr('The point sequence field must be filled in correctly!', 'O campo de sequência dos pontos deve preenchido corretamente!'))


        # Transformacao de Coordenadas Geograficas para Projetadas no sistema UTM
        crsDest = QgsCoordinateReferenceSystem(SRC_Projeto('EPSG'))
        coordinateTransformer = QgsCoordinateTransform()
        coordinateTransformer.setDestinationCrs(crsDest)
        coordinateTransformer.setSourceCrs(vertices.sourceCrs())

        pnts_UTM = {}
        for feat in vertices.getFeatures():
            pnt = feat.geometry().asMultiPoint()[0]
            pnts_UTM[feat['ordem']] = [coordinateTransformer.transform(pnt), feat['tipo'], feat['codigo'], MeridianConvergence(pnt.x(), pnt.y(), crsDest) ]

        # Calculo dos Azimutes e Distancias
        tam = len(pnts_UTM)
        Az_lista, Az_Geo_lista, Dist = [], [], []
        for k in range(tam):
            pntA = pnts_UTM[k+1][0]
            pntB = pnts_UTM[1 if k+2 > tam else k+2][0]
            Az_lista += [(180/pi)*azimute(pntA, pntB)[0]]
            ConvMerediana = pnts_UTM[k+1][3]
            Az_Geo_lista += [(180/pi)*azimute(pntA, pntB)[0]+ConvMerediana]
            Dist += [sqrt((pntA.x() - pntB.x())**2 + (pntA.y() - pntB.y())**2)]

        # Templates HTML
        linha = '''<tr>
          <td>Vn</td>
          <td>En</td>
          <td>Nn</td>
          <td>Ln</td>
          <td>Az_n</td>
          <td>AzG_n</td>
          <td>Dn</td>
        </tr>
        '''

        texto = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
        <html>
        <head>
          <title>''' + self.tr('Descriptive table', str2HTML('Memorial Sintético')) + '''</title>
        </head>
        <body>
        <table
        style="text-align: center; width: 100%; font-size: [FONTSIZE]px; font-family: Arial;"
        border="1" cellpadding="0" cellspacing="0">
        <tbody>
        <tr>
          <td colspan="7" rowspan="1">''' + self.tr('Descriptive table'.upper(), str2HTML('Memorial Sintético'.upper())) + '''[TITULO]</td>
        </tr>
        <tr>
          <td colspan="1" rowspan="2">''' + self.tr('VERTEX', str2HTML('VÉRTICE')) + '''</td>
          <td colspan="2" rowspan="1">''' + self.tr('COORDINATE', str2HTML('COORDENADA')) + '''</td>
          <td colspan="1" rowspan="2">''' + self.tr('SIDE', str2HTML('LADO')) + '''</td>
          <td colspan="2" rowspan="1">''' + self.tr('AZIMUTH', str2HTML('AZIMUTE')) + '''</td>
          <td colspan="1" rowspan="2">''' + self.tr('DISTANCE', str2HTML('DISTÂNCIA')) + '''<br>
        (m)</td>
        </tr>
        <tr>
          <td>E</td>
          <td>N</td>
          <td>''' + self.tr('FLAT', str2HTML('PLANO')) + '''</td>
          <td>''' + self.tr('TRUE', str2HTML('VERDADEIRO')) + '''</td>
        </tr>
        [LINHAS]
        </tbody>
        </table>
        <br>
        </body>
        </html>
        '''

        LINHAS = ''
        if fim == -1 or fim > tam:
            fim = tam
        for k in range(ini-1,fim):
            linha0 = linha
            itens = {'Vn': pnts_UTM[k+1][2],
                        'En': self.tr('{:,.2f}'.format(pnts_UTM[k+1][0].x()), '{:,.2f}'.format(pnts_UTM[k+1][0].x()).replace(',', 'X').replace('.', ',').replace('X', '.')),
                        'Nn': self.tr('{:,.2f}'.format(pnts_UTM[k+1][0].y()), '{:,.2f}'.format(pnts_UTM[k+1][0].y()).replace(',', 'X').replace('.', ',').replace('X', '.')),
                        'Ln': pnts_UTM[k+1][2] + '/' + pnts_UTM[1 if k+2 > tam else k+2][2],
                        'Az_n': self.tr(dd2dms(Az_lista[k],1), dd2dms(Az_lista[k],1).replace('.', ',')),
                        'AzG_n':  self.tr(dd2dms(Az_Geo_lista[k],1), dd2dms(Az_Geo_lista[k],1).replace('.', ',')),
                        'Dn': self.tr('{:,.2f}'.format(Dist[k]), '{:,.2f}'.format(Dist[k]).replace(',', 'X').replace('.', ',').replace('X', '.'))
                        }
            for item in itens:
                linha0 = linha0.replace(item, itens[item])
            LINHAS += linha0
        resultado = texto.replace('[LINHAS]', LINHAS).replace('[TITULO]', str2HTML(titulo.upper())).replace('[FONTSIZE]', str(fontsize))

        output = self.parameterAsFileOutput(parameters, self.HTML, context)
        arq = open(output, 'w')
        arq.write(resultado)
        arq.close()

        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo(self.tr('Leandro Franca - Cartographic Engineer', 'Leandro França - Eng Cart'))

        return {self.HTML: output}