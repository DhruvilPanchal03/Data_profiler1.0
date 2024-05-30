from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .db import get_connection,get_postgres_connection
from .models import my_connector,PostgresConnector,UploadedFile
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from django import forms
import psycopg2
from psycopg2 import OperationalError

@login_required(login_url='login')
def check_conn(request):
    connector = my_connector.objects.filter(user=request.user).first()
    if connector:
        return render(request, 'conapp/connector.html', {'service': connector.service_name, 'connector_id': connector.id})
    
@login_required(login_url='login')
def select_conn(request, connector_id):
    connector = get_object_or_404(my_connector, id=connector_id)
    if connector:
        connection = get_connection(connector.username, connector.host, connector.password)
        if connection and connection.is_connected():
            messages.success(request, 'Connected to MySQL database successfully')
            return redirect('conlist')
    connector = get_object_or_404(my_connector, id=connector_id)
    if connector:
        connection = get_postgres_connection(connector.username, connector.host, connector.password)
        if connection and connection.cursor():
            messages.success(request, 'Connected to MySQL database successfully')
            return redirect('show_all_db')

    messages.error(request, 'Failed to connect to MySQL database')
    return redirect('connectors')

def select_connector(request):
    connectors = ['MYSQL', 'POSTGRESQL','SNOWFLAKE']
    return render(request, 'conapp/select.html', {'connectors': connectors})

@login_required
def connector_details(request):
    if request.method == 'POST':
        selected_connector = request.POST.get('connector')
        request.session['selected_connector'] = selected_connector
        if selected_connector == 'MYSQL':
            return redirect('connectors')
        elif selected_connector == 'POSTGRESQL':
            return redirect('mypsql')
        elif selected_connector == 'SNOWFLAKE':
            return render(request, 'conapp/connector_details.html')
        else:
            pass
    return render(request, 'conapp/select.html')

@login_required
def connectors(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        host = request.POST.get('host')
        service_name = 'mysql'
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.warning(request, 'Confirm password did not match')
        else:
            connection = get_connection(username, host, password)
            if connection and connection.is_connected():
                my_connector.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'username': username,
                        'password': password,
                        'host': host,
                        'service_name': service_name
                    }
                )
                messages.success(request, 'Connected to MySQL database successfully')
                return redirect('conlist')
            else:
                messages.error(request, 'Failed to connect to MySQL database')
    return render(request, 'conapp/connect.html')

@login_required
def mypsql(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        host = request.POST.get('host')
        service_name = 'postgres'
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.warning(request, 'Confirm password did not match')
        else:
            connection = get_postgres_connection(username, host, password)
            if connection:
                try:
                    connection.close()
                    my_connector.objects.update_or_create(
                        user=request.user,
                        defaults={
                            'username': username,
                            'password': password,
                            'host': host,
                            'service_name': service_name
                        }
                    )
                    messages.success(request, 'Connected to PostgreSQL database successfully')
                    return redirect('show_all_db')
                except OperationalError as e:
                    messages.error(request, f'Failed to update PostgreSQL connection details: {e}')
            else:
                messages.error(request, 'Failed to connect to PostgreSQL database')

    return render(request, 'conapp/connect.html')

def show_all_db(request):
    try:
        postgres_connector = my_connector.objects.get(user=request.user)
        
        connection = psycopg2.connect(
            user=postgres_connector.username,
            password=postgres_connector.password,
            host=postgres_connector.host
        )
        
        cursor = connection.cursor()
        cursor.execute('SELECT datname FROM pg_database;')
        databases = [db[0] for db in cursor.fetchall()]
        connection.close()

        return render(request, 'conapp/db_list.html', {'databases': databases})
    
    except my_connector.DoesNotExist:
        messages.error(request, 'PostgreSQL connection details not found')
    except psycopg2.OperationalError as e:
        messages.error(request, f'Failed to connect to PostgreSQL database: {e}')

    return redirect('home')

def show_all_tables(request):
    if request.method == 'POST':
        selected_database = request.POST.get('selected_database')
        try:
            postgres_connector = my_connector.objects.get(user=request.user)
            
            connection = psycopg2.connect(
                user=postgres_connector.username,
                password=postgres_connector.password,
                host=postgres_connector.host,
                database=selected_database
            )
            cursor = connection.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
            tables = [db[0] for db in cursor.fetchall()]
            cursor.close()
            connection.close()
            return render(request, 'conapp/table_list.html', {'tables': tables})
        except my_connector.DoesNotExist:
            messages.error(request, 'PostgreSQL connection details not found')
        except psycopg2.OperationalError as e:
            messages.error(request, f'Failed to connect to PostgreSQL database: {e}')
    return redirect('home')

def show_table_data(request):
    selected_database = request.POST.get('selected_database')
    try:
        selected_tables = request.GET.getlist('tables')
        request.session['selected_tables'] = selected_tables
        postgres_connector = my_connector.objects.get(user=request.user)
        connection = psycopg2.connect(
            user=postgres_connector.username,
            password=postgres_connector.password,
            host=postgres_connector.host,
            database=selected_database
        )
        table_data_list = []
        for table_name in selected_tables:
            cursor = connection.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_catalog=%s;", (selected_database,))
            table_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(table_data, columns=columns)
            metrics = calculate_metrics(df)
            table_data_list.append({'table_name': table_name, 'table_data': table_data, 'columns': columns , 'metrics': metrics})
        return render(request, 'conapp/table_data.html', {'table_data_list': table_data_list})
    except my_connector.DoesNotExist:
        messages.error(request, 'PostgreSQL connection details not found')
    except psycopg2.OperationalError as e:
        messages.error(request, f'Failed to connect to PostgreSQL database: {e}')
    return redirect('home')

def conlist(request):
    connection = get_connection_from_user(request.user)
    if connection and connection.is_connected():
        cursor = connection.cursor()
        cursor.execute('SHOW DATABASES')
        databases = [db[0] for db in cursor.fetchall()]
        return render(request, 'conapp/conlist.html', {'db': databases})
    return HttpResponse("Invalid credentials or no active connection")

def get_connection_from_user(user):
    connector = get_object_or_404(my_connector, user=user)
    return get_connection(connector.username, connector.host, connector.password)

def selectdatabase(request):
    if request.method == 'POST':
        selected_database = request.POST.get('selecteddatabase')
        request.session['selected_database'] = selected_database
        return redirect('tablelist')
    return HttpResponse("Invalid request method")

def tablelist(request):
    selected_database = request.session.get('selected_database')
    connection = get_connection_from_user(request.user)
    if connection and connection.is_connected():
        cursor = connection.cursor()
        cursor.execute(f'USE {selected_database}')
        cursor.execute('SHOW TABLES')
        tables = [table[0] for table in cursor.fetchall()]
        return render(request, 'conapp/tables.html', {'table': tables})
    return HttpResponse("Invalid credentials or no active connection")

def select_table(request):
    if request.method == 'POST':
        selected_table = request.POST.get('selected_table')
        request.session['selected_table'] = selected_table
        return redirect('selected_table', selected_table=selected_table)
    return HttpResponse("Invalid request method")

def calculate_metrics(df):
    metrics = {}

    metrics['num_rows'] = len(df)
    metrics['num_columns'] = len(df.columns)
    metrics['column_names'] = df.columns.tolist()
    metrics['null_values'] = df.isnull().sum().sum()
    metrics['null_values_per_column'] = df.isnull().sum()
    metrics['duplicate_values_per_column'] = {col: sum(df[col].duplicated()) for col in df.columns}
    int_columns = df.select_dtypes(include='integer').columns
    metrics['mean_per_column'] = df[int_columns].mean()
    metrics['median_per_column'] = df[int_columns].median()
    metrics['std_per_column'] = df[int_columns].std()
    return metrics

def selected_table(request, selected_table):
    selected_database = request.session.get('selected_database')
    connection = get_connection_from_user(request.user)
    if connection and connection.is_connected():
        cursor = connection.cursor()
        cursor.execute(f'USE {selected_database}')
        cursor.execute(f'SELECT * FROM {selected_table}')
        table_data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(table_data, columns=columns)
        metrics = calculate_metrics(df)
        return render(request, 'conapp/selected_table.html', {'table_data': table_data, 'columns': columns,'selected_table': selected_table, 'metrics': metrics})
    return HttpResponse("Invalid credentials or no active connection")

def table_view(request):
    selected_connector = request.session.get('selected_connector')
    if selected_connector == 'MYSQL':
        selected_database = request.session.get('selected_database')
        selected_table = request.session.get('selected_table')
        connection = get_connection_from_user(request.user)
        if connection and connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f'USE {selected_database}')
            cursor.execute(f'SELECT * FROM {selected_table}')
            table_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return render(request, 'conapp/table.html', {'table_data': table_data, 'columns': columns, 'selected_table': selected_table})
        return HttpResponse("Invalid credentials or no active connection")
    elif selected_connector == 'POSTGRESQL':
        try:
            selected_tables = request.session.get('selected_tables')
            selected_database = request.session.get('selected_database')
            postgres_connector = my_connector.objects.get(user=request.user)
            
            connection = psycopg2.connect(
                user=postgres_connector.username,
                password=postgres_connector.password,
                host=postgres_connector.host,
                database=selected_database 
            )
            table_data_list = []
            for table_name in selected_tables:
                cursor = connection.cursor()
                cursor.execute(f"SELECT * FROM {table_name};")
                table_data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                table_data_list.append({'table_name': table_name, 'table_data': table_data, 'columns': columns, 'selected_tables': selected_tables})
                return render(request, 'conapp/psql_table.html', {'table_data_list': table_data_list})
        except my_connector.DoesNotExist:
            messages.error(request, 'PostgreSQL connection details not found')
        except psycopg2.OperationalError as e:
            messages.error(request, f'Failed to connect to PostgreSQL database: {e}')
        return HttpResponse("Invalid credentials or no active connection")
    else:
        pass

def charts_view(request):
    selected_connector = request.session.get('selected_connector')
    if selected_connector == 'MYSQL':
        selected_database = request.session.get('selected_database')
        selected_table = request.session.get('selected_table')
        connection = get_connection_from_user(request.user)
        if connection and connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f'USE {selected_database}')
            cursor.execute(f'SELECT * FROM {selected_table}')
            table_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(table_data, columns=columns)

            # Calculate metrics
            metrics = calculate_metrics(df)

    elif selected_connector == 'POSTGRESQL':
        selected_tables = request.session.get('selected_tables')
        postgres_connector = my_connector.objects.get(user=request.user)

        connection = psycopg2.connect(
            user=postgres_connector.username,
            password=postgres_connector.password,
            host=postgres_connector.host,
            database=postgres_connector.database_name
        )

        table_data_list = []
        for table_name in selected_tables:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {table_name};")
            table_data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(table_data, columns=columns)
            table_data_list.append({'table_name': table_name, 'table_data': table_data, 'columns': columns })

        
            metrics = calculate_metrics(df)    
            
    # Unique Values Count Bar Chart
    unique_values_count_trace = go.Bar(
        x=columns,
        y=[df[col].nunique() for col in columns]
    )
    unique_values_count_layout = go.Layout(title='Unique Values Count')
    unique_values_count_fig = go.Figure(data=[unique_values_count_trace], layout=unique_values_count_layout)
    unique_values_count_json = pio.to_json(unique_values_count_fig)

    # Null Values Percentage Pie Chart
    null_values_percentage_trace = go.Pie(
        labels=columns,
        values=[df[col].isnull().mean() for col in columns],
        hoverinfo='label+percent'
    )
    null_values_percentage_layout = go.Layout(title='Null Values Percentage')
    null_values_percentage_fig = go.Figure(data=[null_values_percentage_trace], layout=null_values_percentage_layout)
    null_values_percentage_json = pio.to_json(null_values_percentage_fig)

    # Standard Deviation Bar Chart
    std_per_column_trace = go.Bar(
        x=columns,
        y=metrics['std_per_column']
    )
    std_per_column_layout = go.Layout(title='Standard Deviation per Column')
    std_per_column_fig = go.Figure(data=[std_per_column_trace], layout=std_per_column_layout)
    std_per_column_json = pio.to_json(std_per_column_fig)

    # Box Plot
    box_plot_data = []
    for col in columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            box_plot_trace = go.Box(y=df[col], name=col)
            box_plot_data.append(box_plot_trace)
    box_plot_layout = go.Layout(title='Box Plot')
    box_plot_fig = go.Figure(data=box_plot_data, layout=box_plot_layout)
    box_plot_json = pio.to_json(box_plot_fig)


    return render(request, 'conapp/chartsview.html', {
        'table_data': table_data, 
        'columns': columns,
        'unique_values_count_json': unique_values_count_json,
        'null_values_percentage_json': null_values_percentage_json,
        'std_per_column_json': std_per_column_json,
        'box_plot_json': box_plot_json
    })

def clean_data(df):
    cleaned_df = df.drop_duplicates().fillna(0)  
    return cleaned_df

def download_table(request):
    selected_database = request.session.get('selected_database')
    selected_table = request.session.get('selected_table')
    connection = get_connection_from_user(request.user)
    if connection and connection.is_connected():
        cursor = connection.cursor()
        cursor.execute(f'USE {selected_database}')
        cursor.execute(f'SELECT * FROM {selected_table}')
        table_data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(table_data, columns=columns)
        cleaned_df = clean_data(df)
        csv_data = cleaned_df.to_csv(index=False)
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{selected_table}_cleaned.csv"'
        return response
    return HttpResponse("Invalid credentials or no active connection")

class UploadFileForm(forms.Form):
    file = forms.FileField()

def calculate_metrics_from_file(file):
    df = pd.read_csv(file)
    metrics = calculate_metrics(df)
    return metrics

# def upload_file(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = request.FILES['file']
#             file_name = file.name
#             file_size = file.size
            
#             uploaded_file = UploadedFile.objects.create(
#                 user=request.user,
#                 file=file,
#                 file_name=file_name,
#                 file_size=file_size
#             )

#             metrics = calculate_metrics_from_file(file)
#             return render(request, 'conapp/selected_table.html', {'metrics': metrics})
#     else:
#         form = UploadFileForm()
#     return render(request, 'conapp/upload_file.html', {'form': form})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Process the uploaded file
            metrics = calculate_metrics_from_file(file)
            return render(request, 'conapp/selected_table.html', {'metrics': metrics})
    else:
        form = UploadFileForm()
    return render(request, 'conapp/upload_file.html', {'form': form})