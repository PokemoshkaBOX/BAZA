import dearpygui.dearpygui as dpg
import pyodbc

# Замените значения на свои
server = 'localhost'
database = 'deplomforystu'
username = 'sqluser'
password = '485454'

# Создаем строку подключения
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Подключаемся к базе данных
try:
    conn = pyodbc.connect(connection_string)
    print("Подключение успешно!")
except pyodbc.Error as e:
    print(f"Ошибка при подключении: {e}")

query = "SELECT CAST(D AS date) AS DateOnly, COUNT(*) AS TotalApplications FROM deplomforystu.dbo.applicationsv2 GROUP BY CAST(D AS date) HAVING COUNT(*) > 100;"

# Выполняем запрос
cursor = conn.cursor()
cursor.execute(query)

# Получаем результаты
results = cursor.fetchall()
conn.close()

dates = [item[0] for item in results]
formatted_dates = [str(date) for date in dates]
applications_count = [item[1] for item in results]
print("Массив дат:", formatted_dates)
print("Массив числа заявок:", applications_count)
# Закрываем соединение

# Создаем контекст и представление Dear PyGui
import dearpygui.dearpygui as dpg
import numpy as np

bw = 0.8
my_data = {
    "Massiv dat": applications_count
}
my_colors = {
    "Massiv dat": (200, 0, 30, 255),
}

# Create and bind theme to set the fill color of a bar series
def set_bar_series_color(item, color):
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvBarSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Fill, color, category=dpg.mvThemeCat_Plots)
    dpg.bind_item_theme(item, theme_id)


def cb_draw_stacked_bar_plot(sender, app_data, user_data):
    # Get transformed values of original data in pixel space coordinates relative to top left corner
    trans_x0 = app_data[1][:int(len(app_data[1])/2)]  # x0 values in first half of x value array
    trans_x1 = app_data[1][int(len(app_data[1])/2):]  # x1 values in second half of x value array
    trans_y0 = app_data[2][:int(len(app_data[2])/2)]  # dito for y0 and y1
    trans_y1 = app_data[2][int(len(app_data[2])/2):]
    mouse_x_pixel_space = app_data[0]["MouseX_PixelSpace"]
    mouse_y_pixel_space = app_data[0]["MouseY_PixelSpace"]
    dpg.delete_item(sender, children_only=True, slot=2)
    dpg.push_container_stack(sender)
    dpg.configure_item(item=sender, tooltip=False)

    # Get color of attached theme (theme-> theme component -> theme color)
    theme = dpg.get_item_theme(user_data['dummy_series_item'])
    theme_comp = dpg.get_item_children(theme, slot=1)[0]
    theme_color = dpg.get_value(dpg.get_item_children(theme_comp, slot=1)[0])

    for i, (_x0, _x1, _y0, _y1) in enumerate(zip(trans_x0, trans_x1, trans_y0, trans_y1)):
        dpg.draw_rectangle(pmin=(_x0, _y1), pmax=(_x1, _y0), color=(0, 0, 0, 0), fill=theme_color)
        # Show a tooltip when mouse is hovered over the bar segment at the respective pixel space
        # (Pixel space is starting in upper-left corner)
        if (_x0 < mouse_x_pixel_space < _x1) and (_y1 < mouse_y_pixel_space < _y0):
            dpg.configure_item(item=sender, tooltip=True)
            dpg.set_value(item=user_data["text_item"],
                          value=f"{dpg.get_item_label(user_data['dummy_series_item'])}\n"
                                f"Value: {round(user_data['values'][i], 2)}")
    dpg.pop_container_stack()


def create_stacked_bar_plot(axis, data, colors, bar_width):
    # Return if empty data dict is provided
    if len(data) == 0:
        return
    # Convert the dictionary values to a 2D numpy array
    data_array = np.array(list(data.values()))
    # Calculate the cumulative sum along the column axis
    cumulative_data = np.cumsum(data_array, axis=0)
    # Add a row of zeros at the beginning
    cumulative_data = np.vstack((np.zeros(cumulative_data.shape[1]), cumulative_data))
    # Create arrays for x0 (left side of bar) and x1 (right side of bar)
    x0 = np.arange(data_array.shape[1]) - bar_width / 2
    x1 = np.arange(data_array.shape[1]) + bar_width / 2

    # Loop over all items in the data
    for i, (item_name, item_values) in enumerate(data.items()):
        # Add empty dummy bar series to interact with the custom_series item (change color etc.) because you cannot
        # do it on the custom_series itself without crashing (it's a bug I guess)
        dummy_bar_series = dpg.add_bar_series([], [], parent=axis, label=item_name)
        # Add input text to change the label of a series
        dpg.add_input_text(label="Label", parent=dummy_bar_series, default_value=item_name,
                           callback=lambda s,a: dpg.set_item_label(dpg.get_item_parent(s), a))
        # Add color edit to change the color of a series
        dpg.add_color_edit(label="Color", parent=dummy_bar_series, default_value=colors[item_name], alpha_bar=True,
                           callback=lambda s: set_bar_series_color(dpg.get_item_parent(s), dpg.get_value(s)))
        # Set initially requested color of series
        set_bar_series_color(dummy_bar_series, colors[item_name])

        # Create UUID for text item holding the tooltip later on the custom_series item
        text_item = dpg.generate_uuid()
        # y0: sum of values below item --> bottom; y1: sum of values including item --> top
        y0 = cumulative_data[i]
        y1 = cumulative_data[i+1]
        # Create a custom_series item for every key_item in our data and add a text item to it
        custom_series = dpg.add_custom_series(x=list(x0)+list(x1), y=list(y0)+list(y1), channel_count=2, parent=axis,
                                              callback=cb_draw_stacked_bar_plot,
                                              user_data={"values": item_values,
                                                         "dummy_series_item": dummy_bar_series,
                                                         "text_item": text_item})
        dpg.add_text(tag=text_item, parent=custom_series)

# ----------------------------------------------------------------------------------------------------------------------
# Set up the main DeapPyGui Window, add a plot with X and Y axis and add a stacked bar plot to the axis
dpg.create_context()
dpg.create_viewport(title="Custom series test", width=1400, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.maximize_viewport()
dpg.add_window(tag="main_window")
dpg.set_primary_window(window="main_window", value=True)
# Add a plot item with axis and legend to the main_window item
dpg.add_plot(tag="plot_item", height=-1, width=-1, parent="main_window")
dpg.add_plot_legend(parent="plot_item")
dpg.add_plot_axis(dpg.mvXAxis, tag="xaxis", parent="plot_item")
dpg.add_plot_axis(dpg.mvYAxis, tag="yaxis", parent="plot_item")
# Add the stacked bar plot
create_stacked_bar_plot(axis="yaxis", data=my_data, colors=my_colors, bar_width=bw)

dpg.start_dearpygui()
dpg.destroy_context()