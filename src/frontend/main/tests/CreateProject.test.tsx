import React from 'react';
import { act, render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PrimaryAppBar from '../src/utilities/PrimaryAppBar';
import { Provider } from 'react-redux';
import { store } from '../src/store/Store.js';
import { BrowserRouter } from 'react-router-dom';
export const renderWithRouter = (ui, { route = '/' } = {}) => {
  act(() => window.history.pushState({}, 'Test page', route));

  return {
    ...render(ui, { wrapper: BrowserRouter }),
  };
};
jest.mock('axios'); // Mock axios module

describe('MyComponent', () => {
  test('renders the app bar with correct elements', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <PrimaryAppBar />
        </BrowserRouter>
      </Provider>,
    );

    // Check if the "EXPLORE PROJECTS" tab is rendered
    const exploreTabElement = screen.getByText('EXPLORE PROJECTS');
    expect(exploreTabElement).toBeInTheDocument();

    // Check if the "MANAGE ORGANIZATIONS" tab is rendered
    const manageOrgTabElement = screen.getByText('MANAGE ORGANIZATIONS');
    expect(manageOrgTabElement).toBeInTheDocument();
  });
});
