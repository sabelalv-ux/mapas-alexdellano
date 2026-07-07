# PANEL 2: ACCIONES DEFENSIVAS Y OFENSIVAS
            defensivas = df_player[df_player['type_name'].isin(['Tackle', 'Interception', 'Clearance', 'BallRecovery'])]
            ofensivas = df_player[(df_player['type_name'].isin(['TakeOn', 'FoulGiven'])) | ((df_player['type_name'] == 'Pass') & (df_player['x'] > 50))]

            # Dibujar polígono defensivo (DF) solo si hay 3 o más acciones
            if len(defensivas) >= 3:
                pitch.convex_hull(defensivas['x'], defensivas['y'], ax=axs[1], facecolor='#0077b6', alpha=0.4, edgecolor='#00b4d8', linewidth=2)
            # Siempre dibujamos los puntos, aunque sea uno solo
            if len(defensivas) > 0:
                pitch.scatter(defensivas['x'], defensivas['y'], color='#00b4d8', s=40, ax=axs[1], zorder=3)
            
            # Dibujar polígono ofensivo (OF) solo si hay 3 o más acciones
            if len(ofensivas) >= 3:
                pitch.convex_hull(ofensivas['x'], ofensivas['y'], ax=axs[1], facecolor='#38b000', alpha=0.4, edgecolor='#70e000', linewidth=2)
            # Siempre dibujamos los puntos ofensivos
            if len(ofensivas) > 0:
                pitch.scatter(ofensivas['x'], ofensivas['y'], color='#70e000', s=40, ax=axs[1], zorder=3)

            axs[1].text(50, 30, "DF", color='white', weight='bold', bbox=dict(facecolor='#0077b6', edgecolor='none', boxstyle='round,pad=0.4'))
            axs[1].text(50, 70, "OF", color='white', weight='bold', bbox=dict(facecolor='#38b000', edgecolor='none', boxstyle='round,pad=0.4'))
