# Importo las librerías necesarias para llevar acabo el programa
import pandas as pd
import numpy as np
import math
from IPython.display import display

# Creo la función que va a analizar los datos del dataset
def analisis_datos(data_dictionary, order_details, orders, pizzas, pizza_types):
    lista_dataframes = [data_dictionary, order_details, orders, pizzas, pizza_types]
    df_analisis = [] 
    for dataframe in lista_dataframes:
        # Para cada archivo, creo un dataframe para añadir el analisis de ese df
        df = pd.DataFrame()
        # Añado la columna de los tipos de datos de cada columna del df
        df['tipos_de_datos'] = dataframe.dtypes
        # Añado la columna de los datos nan que hay en cada columna del df 
        df['datos_nan'] = dataframe.isna().sum()
        # Calculo el porcentaje de datos nan que existe en total en el df
        porcentaje_nan = int((df['datos_nan'].sum() / dataframe.shape[0])*100)
         # Añado la columna de los datos null que hay en cada columna del df 
        df['datos_null'] = dataframe.isnull().sum()
        # Calculo el porcentaje de datos null que existe en total en el df
        porcentaje_null = int((df['datos_null'].sum() / dataframe.shape[0])*100)
        datos_nulos = []
        # Calculo en número de Nones que hay en cada columna
        for column in dataframe:
            contador = 0
            for i in range(len(column)):
                if column[i] == None:
                    contador += 1
            datos_nulos.append(contador)
        # Añado la columna de los datos None que hay en cada columna del df
        df['datos_none'] = datos_nulos 
        # Calculo el porcentaje de datos none que existe en total en el df
        porcentaje_none = int((sum(datos_nulos) / dataframe.shape[0])*100)
        # Añado en mi df una fila al final con todos los porcentajes
        porcentajes = pd.Series(data = {'tipos_de_datos': None, 'datos_nan': porcentaje_nan, 'datos_null': porcentaje_null, 'datos_none': porcentaje_none }, name = 'Porcentaje')
        df = df.append(porcentajes) 
        # Añado cada df del análisis de los datos en la lista que vamos a devolver
        df_analisis.append(df)
    return df_analisis

def arreglar_dataframes(orders, order_details, pizzas, pizza_types): # Creo la función que va a formatear los datos para devolverlos como queremos 
    orders['date'] = pd.to_datetime(orders['date'], format = "%d/%m/%Y") # Tansformo la columna de las fechas en el formato indicado 
    order_details = order_details.merge(orders, on = 'order_id') # Junto los df de los orders y los orders_details para poder trabajar con todo a la vez
    order_details['week number'] = None # Creo una columna que va a guardar el número de la semana
    for fecha in range(0,len(order_details['date'])): 
        # Para cada pedido añado la semana en la que se ha dado ese pedido
        numero_semana = int(order_details['date'].iloc[fecha].strftime('%W')) 
        order_details['week number'].iloc[fecha] = numero_semana
    pizzas = pizzas.merge(pizza_types, on = 'pizza_type_id') # Junto los df con los detalles de cada pizza
    return order_details, pizzas # Devuelvo los dfs transformador y con los datos formateados

def ingredientes_pizzas(pizzas): # Creo la función que guarda en un dataframe qué ingredientes tiene cada pizza
    tipos_pizza = pizzas['pizza_id'].unique().tolist() # Establezco los tipos de pizza que existen en el restaurante
    ingredientes = set() # Creo un set en el que voy a añadir los ingredientes que se pueden añadir a las pizzas
    for i in range(len(pizzas)): 
        # Recorro el dataframe añadiendo a mi set los ingredientes de forma única
        for ing in [ing.strip() for ing in pizzas['ingredients'].iloc[i].split(',')]:
            ingredientes.add(ing)
    matriz = [] # Creo la matriz que va a definir mi dataframe de las pizzas con sus ingredientes
    for fila in range(len(pizzas)): # Para cada fila del df de las pizzas
        tipo = [] 
        for ingrediente in ingredientes:
            # Para cada tipo de pizza guardo un 1 si contiene al ingrediente o un 0 si no
            if ingrediente in [ing.strip() for ing in pizzas['ingredients'].iloc[fila].split(",")]:
                tipo.append(1)
            else:
                tipo.append(0)
        matriz.append(tipo)
    matriz = np.array(matriz)
    # Creo el dataframe en el que las filas son los tipos de pizza (distinguiendo por tamaño) y las columnas son cada uno de los ingredientes
    ingre_pizzas = pd.DataFrame(data = matriz, index = tipos_pizza, columns = ingredientes)
    return ingre_pizzas

def ingredientes_semana(order_details, ingre_pizzas): # Creo la función que me calcula la cantidad de cada ingrediente por semana
    semanas = []
    multiplicadores = {'s': 1, 'm': 2, 'l': 3} 
    # Establezco que si la pizza es mediana necesite el doble de cantidad que una pizza pequeña y que si es grande necesite el triple
    orders_week = order_details.groupby(by= 'week number') # Divido todos los pedidos por semanas
    for week in orders_week: 
        # Para cada semana creo una copia de la tabla que indica que ingredientes tiene cada pizza para completarla con la semana en cuestion 
        df_nuevo = ingre_pizzas.copy()
        # Creo una tabla de contingencia para contar el número de pizzas de cada tipo que hay según el número por pedido
        contingencia = pd.crosstab(week[1].pizza_id, week[1].quantity)
        indices = contingencia.index # Guardo los nombres de las pizzas
        for indice in indices: 
            # Para cada tipo de pizza guardo el multiplicador, es decir, el valor por el que voy a multiplicar en función del tamaño de la pizza 
            multiplicador = multiplicadores[indice[-1]]
            numero = 0
            columnas = contingencia.columns
            # Calculo el número de pizzas de cada tipo por semana en proporción a si todas fuesen de tamaño pequeño 
            for columna in columnas: 
                numero += (contingencia[columna][indice]) * columna
            # Multiplico la fila del dataframe que guarda que ingredientes contiene cada pizza por el número de pizzas que tengo que hacer esa semana
            df_nuevo.loc[indice] = df_nuevo.loc[indice].mul(multiplicador*numero)
        # Devuelvo una lista con todos los df de los ingredientes por semana
        semanas.append(df_nuevo)
    return semanas

def crear_recuento_semana(semanas): # Creo la función que me hace un recuento de los ingredientes por semana
    diccionario = {} 
    for semana in semanas: 
        columnas = semana.columns
        # Para cada semana hago el recuento de cada ingrediente y lo añado  a diccionario que contiene como claves los ingredientes y como valores
        # una lista con la cantidad del ingrediente necesaria para cada semana en función del número de pizzas (cada posicion de la lista es una semana)
        for columna in columnas:
            if columna not in diccionario:
                diccionario[columna] = []
            contador = semana[columna].sum()
            diccionario[columna].append(contador)
    # Devuelvo el diccionario con todos los ingredientes y sus respectivas cantidades
    return diccionario

def extract(): # Creo la función que extrae los datos (la E de mi ETL)
    # Guardo cada archivo de tipo .csv en un dataframe, teniendo en cuenta el encoding necesario para que lo pueda leer sin problemas
    data_dictionary = pd.read_csv('data_dictionary.csv')
    order_details = pd.read_csv('order_details.csv')
    orders = pd.read_csv('orders.csv')
    pizzas = pd.read_csv('pizzas.csv')
    pizza_types = pd.read_csv('pizza_types.csv', encoding = 'unicode_escape')
    return data_dictionary, order_details, orders, pizzas, pizza_types

def transform(data_dictionary, order_details, orders, pizzas, pizza_types): 
    # Creo la función que transforma los datos y realiza la predicción (la T de mi ETL)
    df_analisis = analisis_datos(data_dictionary, order_details, orders, pizzas, pizza_types) # Llamo a la función que me analiza los datos
    # LLamo a la función que me formatea los dataframes y los datos 
    order_details, pizzas = arreglar_dataframes(orders, order_details, pizzas, pizza_types) 
    ingre_pizzas = ingredientes_pizzas(pizzas) # Llamo a la función que me genera el dataframe con los ingredientes que contiene cada pizza
    # Llamo a la función que me genera un df por cada semana con los ingredientes necesarios para dicha semana
    semanas = ingredientes_semana(order_details, ingre_pizzas) 
    # Creo el diccionario que contiene para cada ingrediente una lista con la cantidad necesaria para cada semana
    diccionario = crear_recuento_semana(semanas) 
    return df_analisis, diccionario # Devuelvo el df con el analisis de los datos y una lista con los dfs de los ingredientes

def load(df_analisis, diccionario): # Cargo los resultados en dos datafrmes y los imprimo por pantalla
    nombres = ['data_dictionary_analisis.csv', 'order_details_analisis.csv', 'orders_analisis.csv', 'pizzas_analisis.csv', 'pizza_types_analisis.csv']
    for df in range(len(df_analisis)): # Para cada archivo leído devuelvo un dataframe con el informe de calidad de los datos y lo imprimo por pantalla
        df_analisis[df].to_csv(nombres[df], index = False)
        display(df_analisis[df])
    dict_medias = {}
    for clave in diccionario: # Para cada ingrediente predigo la cantidad necesaria en una semana 
        # Para predecir los ingredientes necesarios por semana hago la media de los necesitados en cada semana del año
        dict_medias[clave] = math.ceil(np.array(diccionario[clave]).mean()) 
    # Creo un dataframe con el reporte en el que las columnas son los ingredientes, la cantidad en función del número de pizzas en proporción a
    # todas de tamaño s, la cantidad en gramos suponinedo que de cada ingrediente echas 50 gr a cada pizza pequeña y la cantidad en kilos de la misma manera
    df = pd.DataFrame([[clave, dict_medias[clave], dict_medias[clave]*50, dict_medias[clave]*50 / 1000] for clave in dict_medias.keys()], columns=['Ingrediente', 'Nº pizzas en proporción todas s', 'Cantidad en gramos(50 gr/pizza)', 'Cantidad en kilos'])
    df.to_csv('reporte_ingredientes_2015.csv', index= False) # Creo el csv con la predicción
    display(df) # Muestro la predicción por pantalla

if __name__ == "__main__":
    # Creo una ETL que lleva a cabo mi programa
    data_dictionary, order_details, orders, pizzas, pizza_types = extract() # Llamo a extract para extraer todos los datos 
    # LLamo a transform para calcular todos los ingredientes necesarios por semana
    df_analisis, media_ingredientes = transform(data_dictionary, order_details, orders, pizzas, pizza_types)
    load(df_analisis, media_ingredientes) # LLamo a load para hacer la predicción y cargarsela al cliente en un formato csv y por pantalla

