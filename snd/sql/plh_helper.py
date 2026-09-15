


class PLH_Plotter:

    def __init__(self, data):
        pass

    def formatData(self, data):
            # Format the dict of dataframes
            if type(data) is not dict or len(data) == 0:    
                return None
            
            one_dataset = list(data.copy().values())[0]
            plottable_data = {key:val for key,val in one_dataset.items() if key != 'settings'}
            master_df = pd.DataFrame()
            
            random_sheet = next(iter(plottable_data.values()))
            min_frequency = random_sheet.index[0]
            max_frequency = random_sheet.index[-1]
            num_points = len(random_sheet.index)
            min_input_power = min(plottable_data.keys())
            max_input_power = max(plottable_data.keys())
                
            power_df = plottable_data[max_input_power]
            rf_mult = int(power_df.mean().idxmax())
            
            for input_power_key, df_value in plottable_data.items():
                df_value.columns = df_value.columns.map(int)
                input_power_key = float(input_power_key)

                dbc_df = df_value.sub(df_value[rf_mult], axis=0)
                dbc_df = dbc_df.drop(rf_mult, axis=1)

                df_value['worst_harmonic_values'] = dbc_df.max(axis=1)
                df_value['worst_harmonic_tones'] = dbc_df.idxmax(axis=1)

                df_value.update(dbc_df)
                df_value = df_value.rename(columns={rf_mult: "output_power"})
                df_value[rf_mult] = 0
                df_value['input_power'] = input_power_key

                every_nth_row = 20
                df_value = df_value.iloc[::every_nth_row, :]

                master_df = pd.concat([master_df, df_value])
            
            return master_df

    def _createFigure(self):
            fig = make_subplots(rows=1, cols=2, subplot_titles=("Worst Harmonic dBc Values", "Harmonics by Output Power"))
            
            df = self.formatData(self.data).sort_index()
            
            left_row = df['output_power']
            left_col = df['worst_harmonic_values']
            left_display_text = [
                f"Harmonic: {harmonic}<br>Frequency (GHz): {frequency:.2f}"
                for harmonic, frequency in zip(
                    df['worst_harmonic_tones'],
                    df.index
                )
            ]
            
            fig.add_trace(
                go.Scatter(
                    x=left_row,
                    y=left_col,
                    mode='markers',
                    text=left_display_text,
                    hoverinfo='text',
                    marker=dict(
                        size=6,
                        color=df.index,
                        colorscale="agsunset",
                        colorbar=dict(title="Freq (GHz)", len=0.75, xanchor="left", x=0.46)
                    ),
                    showlegend=False,
                    name="Worst Harmonics (dBc)"
                ),
                row=1, col=1
            )
            fig.update_xaxes(title_text="Output RF Power (dBm)", row=1, col=1)
            fig.update_yaxes(title_text="Worst Harmonic Power (dBc)", row=1, col=1)
            
            right_cols = [col for col in df.columns if isinstance(col, (int, float))]
            output_power_list = list(range(int(df['output_power'].min()), int(df['output_power'].max() + 1)))
            
            # Determine active output power up front so initial traces match the active slider step
            try:    used_output_power_list = output_power_list[-80:]
            except: used_output_power_list = output_power_list
            active_output_power = used_output_power_list[-2]
            
            right_trace_indices = []
            
            for col in right_cols:
                active_df = df.loc[abs(df['output_power'] - active_output_power) <= 0.5,
                                   [col, 'input_power', 'output_power']].sort_index()
                
                right_display_text = [
                    f"Input Power (dBm): {input_power:.2f}<br>Output Power (dBm): {output_power:.2f}"
                    for input_power, output_power in zip(
                        active_df['input_power'],
                        active_df['output_power']
                    )
                ]
                
                fig.add_trace(
                    go.Scatter(
                        x=active_df.index,
                        y=active_df[col],
                        text=right_display_text,
                        hoverinfo='text',
                        mode='markers',
                        showlegend=True,
                        name=col
                    ),
                    row=1, col=2
                )
                right_trace_indices.append(len(fig.data) - 1)
            
            fig.update_xaxes(title_text="Frequency (GHz)", row=1, col=2)
            fig.update_yaxes(title_text="Output RF Power (dBc)", row=1, col=2)
            fig.update_yaxes(range=[-100, 10], row=1, col=2)
            
            # Set initial shape and title to match active step
            fig.add_shape(
                type="line",
                x0=active_output_power,
                x1=active_output_power,
                y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(width=2)
            )
            
            fig.layout.annotations[1].update(text=f"Harmonics (dBc) at {int(active_output_power)} dBm Output Power")
            
            steps = []
            for index, output_power in enumerate(used_output_power_list):
                dataset = df[abs(df['output_power'] - output_power) <= 0.5].sort_index()
                
                right_cols = [col for col in dataset.columns if isinstance(col, (int, float))]
                
                x_data = [dataset.index for col in right_cols]
                y_data = [dataset[col] for col in right_cols]
                
                subplot_annotation_list = [annotation.to_plotly_json() for annotation in fig.layout.annotations]
                subplot_annotation_list[1]["text"] = f"Harmonics (dBc) at {int(output_power)} dBm Output Power"
                
                right_display_text = [
                    f"Input Power (dBm): {input_power:.2f}<br>Output Power (dBm): {output_power:.2f}"
                    for input_power, output_power in zip(
                        dataset['input_power'],
                        dataset['output_power']
                    )
                ]
                
                args = [
                    {"x": x_data, "y": y_data, "text": right_display_text},
                    {
                        "annotations": subplot_annotation_list,
                        "shapes[0].x0": output_power,
                        "shapes[0].x1": output_power
                    },
                    right_trace_indices
                ]
                
                steps.append(dict(
                    method="update",
                    label=str(output_power),
                    args=args
                ))
            
            fig.update_layout(
                sliders=[{
                    'active': len(steps) - 2,
                    'currentvalue': {"prefix": "Output Power (dBm): "},
                    'pad': {"t": 50},
                    'x': 0,
                    'y': -0.2,
                    'yanchor': 'bottom',
                    'xanchor': 'left',
                    'len': 1.0,
                    'steps': steps
                }],
                title=dict(
                    text='<u>' + self.title + '</u>',
                    font=dict(family="sans-serif", size=30, color="black")
                )
            )
            
            return fig